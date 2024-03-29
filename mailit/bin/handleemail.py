# coding=utf-8
import email
import re
import requests
from requests.auth import AuthBase
import logging
import sys
import config
import json
from email_reply_parser import EmailReplyParser
from flufl.bounce import all_failures, scan_message
from mailit.models import RawIncomingEmail
from nuntium.models import Answer
from mailit.bin.froide_email_utils import FroideEmailParser
from mailit.exceptions import CouldNotFindIdentifier, TemporaryFailure
from django.conf import settings

logging.basicConfig(filename='mailing_logger.txt', level=logging.INFO)


class ApiKeyAuth(AuthBase):
    """
    Sets the appropriate authentication headers
    for the Tastypie API key authentication.
    """
    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key

    def __call__(self, r):
        r.headers['Authorization'] = 'ApiKey %s:%s' % (self.username, self.api_key)
        return r


class EmailReportBounceMixin(object):
    def report_bounce(self):
        data = {'key': self.outbound_message_identifier}
        headers = {'content-type': 'application/json'}
        self.requests_session.post(
            config.WRITEIT_API_WHERE_TO_REPORT_A_BOUNCE,
            data=json.dumps(data),
            headers=headers,
            )


class EmailSaveMixin(object):
    def save(self):
        data = {
            'key': self.outbound_message_identifier,
            'content': self.content_text,
            'format': 'json',
            }
        headers = {'content-type': 'application/json'}
        result = self.requests_session.post(config.WRITEIT_API_ANSWER_CREATION, data=json.dumps(data), headers=headers)
        log = "When sent to %(location)s the status code was %(status_code)d"
        log = log % {
            'location': config.WRITEIT_API_ANSWER_CREATION,
            'status_code': result.status_code,
            }
        logging.info(log)
        answer = None
        try:
            answer_id = json.loads(result.content)['id']
            answer = Answer.objects.get(id=answer_id)
        except Exception:
            pass
        return answer

    def save_attachment(self, answer, attachment):
        pass


class EmailAnswer(EmailSaveMixin, EmailReportBounceMixin):
    def __init__(self):
        self.subject = ''
        self._content_text = ''
        self.content_html = ''
        self.outbound_message_identifier = ''
        self.email_from = ''
        self.email_to = ''
        self.when = ''
        self.message_id = None  # http://en.wikipedia.org/wiki/Message-ID
        self.requests_session = requests.Session()
        username = config.WRITEIT_USERNAME
        apikey = config.WRITEIT_API_KEY
        self.requests_session.auth = ApiKeyAuth(username, apikey)
        self.is_bounced = False
        self.attachments = []

    def get_content_text(self):
        cleaned_content = self._content_text
        # pattern = '[\w\.-]+@[\w\.-]+'
        # expression = re.compile(pattern)
        # cleaned_content = re.sub(expression, '', cleaned_content)
        if self.email_to:
            email_to = re.escape(self.email_to)
            expression = re.compile(" ?\n".join(email_to.split()))
            # Joining the parts of the "To" header with a new line
            # So if for example the "To" header comes as follow
            # Felipe Álvarez <giant-email@tremendous-email.org>
            # it would match in the content the following
            # Felipe
            # Álvarez
            # <giant-email@tremendous-email.org>
            # This is to avoid things like the one in #773
            cleaned_content = expression.sub('', cleaned_content)
        cleaned_content = re.sub(r'[\w\.-\.+]+@[\w\.-]+', '', cleaned_content)

        cleaned_content = cleaned_content.replace(self.outbound_message_identifier, '')
        return cleaned_content

    def set_content_text(self, value):
        self._content_text = value

    content_text = property(get_content_text, set_content_text)

    def send_back(self):
        if self.is_bounced:
            if settings.FLAG_BOUNCED_CONTACTS:
                self.report_bounce()
        else:
            answer = self.save()
            raw_answers = RawIncomingEmail.objects.filter(message_id=self.message_id)
            if answer is not None:
                for attachment in self.attachments:
                    self.save_attachment(answer, attachment)
                if raw_answers:
                    raw_email = raw_answers[0]
                    raw_email = RawIncomingEmail.objects.get(message_id=self.message_id)
                    raw_email.answer = answer
                    raw_email.save()
                return answer

    def add_attachment(self, attachment):
        self.attachments.append(attachment)

def get_outbound_message_identifier(the_recipient):
    """
    Get the OutboundMessageIdentifier key from the recipients/"To" value of 
    an incoming email.

    It tries to find the first email that contains a "+" and returns the part
    after the "+" and before the "@". For example, for 'admin+12345@pa.org.za"
    it will return "12345".

    :param the_recipient: String value containing the recipient(s) of the email
        separated by commas. For example:
        "Zene Van niekerk <south-africa-assembly+25459cface3411eaa5e00242ac110006@writeinpublic.pa.org.za>, 
        Nomsa Tarabella-Marchesi <nomsa_marchesi@hotmail.com>"
    
    :raises CouldNotFindIdentifier: if it can't find an identifier in the
        recipient value.
    """
    regex = re.compile(r"\w+[\+\-](\w+?)@")
    the_match = regex.search(the_recipient)
    if the_match is None:
        raise CouldNotFindIdentifier
    return the_match.groups()[0]


class EmailHandler(FroideEmailParser):
    def __init__(self, answer_class=EmailAnswer):
        self.message = None
        self.answer_class = answer_class
        self.content_types_attrs = {
            'text/plain': 'content_text',
            'text/html': 'content_html',
        }

    def save_raw_email(self, lines):
        return RawIncomingEmail.objects.create(content=lines)

    def instanciate_answer(self, lines):
        answer = self.answer_class()
        msgtxt = ''.join(lines)

        msg = email.message_from_string(msgtxt)
        temporary, permanent = all_failures(msg)

        if permanent:
            answer.is_bounced = True
            answer.email_from = scan_message(msg).pop()
        elif temporary:
            raise TemporaryFailure
        else:
            answer.email_from = msg["From"]

        the_recipient = msg["To"]
        answer.subject = msg["Subject"]
        answer.when = msg["Date"]
        answer.message_id = msg["Message-ID"]

        the_recipient = re.sub(r"\n", "", the_recipient)

        answer.outbound_message_identifier = get_outbound_message_identifier(the_recipient)
        answer.email_to = the_recipient
        logging.info("Reading the parts")
        for part in msg.walk():
            logging.info("Part of type " + part.get_content_type())

            content_type_attr = self.content_types_attrs.get(part.get_content_type())
            if content_type_attr:
                charset = part.get_content_charset() or "ISO-8859-1"
                data = part.get_payload(decode=True).decode(charset)

                setattr(
                    answer,
                    content_type_attr,
                    EmailReplyParser.parse_reply(data).strip(),
                    )
            else:
                self.handle_not_processed_part(part)

            attachment = self.parse_attachment(part)
            if attachment:
                answer.add_attachment(attachment)

        log = 'New incoming email from %(from)s sent on %(date)s with subject %(subject)s and content %(content)s'
        log = log % {
            'from': answer.email_from,
            'date': answer.when,
            'subject': answer.subject,
            'content': answer.content_text,
            }
        logging.info(log)
        return answer

    def handle_not_processed_part(self, part):
        pass

    def set_raw_email_with_processed_email(self, raw_email, email_answer):
        raw_email.message_id = email_answer.message_id
        raw_email.save()

    def handle(self, lines):
        raw_email = self.save_raw_email(lines)
        email_answer = self.instanciate_answer(lines)
        self.set_raw_email_with_processed_email(raw_email, email_answer)

        return email_answer


if __name__ == '__main__':  # pragma: no cover
    lines = sys.stdin.readlines()
    handler = EmailHandler()
    answer = handler.handle(lines)
    answer.send_back()
    sys.exit(0)
