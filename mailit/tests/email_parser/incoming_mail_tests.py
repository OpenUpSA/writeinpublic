# coding=utf-8
import json
from mock import patch
from requests.models import Request

from django.utils.unittest import skip
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from nuntium.models import OutboundMessage, OutboundMessageIdentifier, Message, OutboundMessagePluginRecord, Answer
from contactos.models import Contact

from global_test_case import GlobalTestCase as TestCase
from global_test_case import ResourceGlobalTestCase as ResourceTestCase
from mailit.answer import OutboundMessageAnswer
from mailit.bin import config
from mailit.bin.handleemail import (
    EmailHandler, EmailAnswer, ApiKeyAuth, get_outbound_message_identifier
)
from mailit.exceptions import CouldNotFindIdentifier
from mailit.models import BouncedMessageRecord
from django.test.utils import override_settings


class PostMock():
    def __init__(self):
        self.status_code = 201


class TestApiKeyAuthentification(TestCase):
    def setUp(self):
        super(TestApiKeyAuthentification, self).setUp()
        self.user = User.objects.get(id=1)
        self.api_key = self.user.api_key

    def test_creation(self):
        auth = ApiKeyAuth(username=self.user.username, api_key=self.api_key.key)
        self.assertTrue(auth)
        self.assertEquals(auth.username, self.user.username)
        self.assertEquals(auth.api_key, self.api_key.key)

    def test_set_headers(self):
        auth = ApiKeyAuth(username=self.user.username, api_key=self.api_key.key)
        req = Request()
        req = auth.__call__(req)
        self.assertTrue('Authorization' in req.headers)
        expected_headers = 'ApiKey %s:%s' % (self.user.username, self.api_key.key)
        self.assertEquals(req.headers['Authorization'], expected_headers)


class ReplyHandlerTestCase(ResourceTestCase):
    def setUp(self):
        super(ReplyHandlerTestCase, self).setUp()
        self.user = User.objects.get(id=1)
        f = open('mailit/tests/fixture/reply_mail.txt')
        self.email = f.readlines()
        f.close()
        self.where_to_post_creation_of_the_answer = 'http://localhost:8000/api/v1/create_answer/'
        config.WRITEIT_API_ANSWER_CREATION = self.where_to_post_creation_of_the_answer
        config.WRITEIT_API_KEY = self.user.api_key.key
        config.WRITEIT_USERNAME = self.user.username
        self.handler = EmailHandler()

    def test_get_only_new_content_and_not_original(self):
        answer = self.handler.handle(self.email)
        self.assertEquals(answer.content_text, u"aass áéíóúñ")


class DoesNotIncludeTheIdentifierInTheContent(TestCase):
    def setUp(self):
        super(DoesNotIncludeTheIdentifierInTheContent, self).setUp()
        self.user = User.objects.get(id=1)
        f = open('mailit/tests/fixture/mail_with_identifier_in_the_content.txt')
        self.email = f.readlines()
        f.close()
        self.where_to_post_creation_of_the_answer = 'http://localhost:8000/api/v1/create_answer/'
        config.WRITEIT_API_ANSWER_CREATION = self.where_to_post_creation_of_the_answer
        config.WRITEIT_API_KEY = self.user.api_key.key
        config.WRITEIT_USERNAME = self.user.username
        self.handler = EmailHandler()

    def test_does_not_contain_the_identifier_when_posting(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.requests_session.auth.api_key, self.user.api_key.key)
        self.assertEquals(self.answer.requests_session.auth.username, self.user.username)
        expected_headers = {'content-type': 'application/json'}
        data = {
            'key': self.answer.outbound_message_identifier,
            'content': self.answer.content_text,
            'format': 'json',
            }

        data = json.dumps(data)

        self.assertFalse(self.answer.outbound_message_identifier in self.answer.content_text)
        self.assertNotIn("prueba+@mailit.ciudadanointeligente.org", self.answer.content_text)
        with patch('requests.Session.post') as post:
            post.return_value = PostMock()
            self.answer.send_back()

            post.assert_called_with(self.where_to_post_creation_of_the_answer, data=data, headers=expected_headers)


class GetOutboundMessageIdentifierTestCase(TestCase):
    def test_get_identifier_from_one_email(self):
        recipient = "test+12345@gmail.com"
        result = get_outbound_message_identifier(recipient)
        self.assertEquals(result, "12345")

    def test_raise_exception_for_no_identifier_found(self):
        recipient = "test@gmail.com"

        with self.assertRaises(CouldNotFindIdentifier):
            result = get_outbound_message_identifier(recipient)

    def test_get_identifier_from_multiple_emails(self):
        recipient = "Zene Van niekerk <south-africa-assembly+25459cface3411eaa5e00242ac110006@writeinpublic.pa.org.za>, Nomsa Tarabella-Marchesi <nomsa_marchesi@hotmail.com>"
        result = get_outbound_message_identifier(recipient)
        self.assertEquals(result, "25459cface3411eaa5e00242ac110006")

@override_settings(FLAG_BOUNCED_CONTACTS = True)
class IncomingEmailHandlerTestCase(ResourceTestCase):
    def setUp(self):
        super(IncomingEmailHandlerTestCase, self).setUp()
        self.user = User.objects.get(id=1)
        f = open('mailit/tests/fixture/mail.txt')
        self.email = f.readlines()
        f.close()
        self.where_to_post_creation_of_the_answer = 'http://localhost:8000/api/v1/create_answer/'
        config.WRITEIT_API_ANSWER_CREATION = self.where_to_post_creation_of_the_answer
        config.WRITEIT_API_KEY = self.user.api_key.key
        config.WRITEIT_USERNAME = self.user.username
        self.handler = EmailHandler()

    def test_gets_the_subject(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.subject, 'prueba4')

    def test_gets_the_content(self):
        self.answer = self.handler.handle(self.email)
        self.assertTrue(self.answer.content_text.startswith('prueba4lafieri'))

    def test_get_html_content(self):
        '''Getting the html content out of a mail'''
        self.answer = self.handler.handle(self.email)
        self.assertIn('prueba4lafieri', self.answer.content_html)

    def test_gets_the_outbound_message_identifier_to_which_relate_it(self):
        #make a regexp
        #ask maugsbur about it
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.outbound_message_identifier, "4aaaabbb")

    def test_gets_who_sent_the_email(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.email_from, '=?ISO-8859-1?Q?Felipe_=C1lvarez?= <falvarez@ciudadanointeligente.cl>')

    def test_gets_when_it_was_sent(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.when, 'Wed, 26 Jun 2013 17:05:30 -0400')

    def test_it_posts_to_the_api(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.requests_session.auth.api_key, self.user.api_key.key)
        self.assertEquals(self.answer.requests_session.auth.username, self.user.username)
        expected_headers = {'content-type': 'application/json'}
        data = {
            'key': self.answer.outbound_message_identifier,
            'content': self.answer.content_text,
            'format': 'json'
            }
        data = json.dumps(data)
        with patch('requests.Session.post') as post:
            post.return_value = PostMock()
            self.answer.send_back()

            post.assert_called_with(self.where_to_post_creation_of_the_answer, data=data, headers=expected_headers)

    def test_it_posts_to_the_api_using_the_method_post_to_the_api(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.requests_session.auth.api_key, self.user.api_key.key)
        self.assertEquals(self.answer.requests_session.auth.username, self.user.username)
        expected_headers = {'content-type': 'application/json'}
        data = {
            'key': self.answer.outbound_message_identifier,
            'content': self.answer.content_text,
            'format': 'json',
            }
        data = json.dumps(data)
        with patch('requests.Session.post') as post:
            post.return_value = PostMock()
            self.answer.save()

            post.assert_called_with(self.where_to_post_creation_of_the_answer, data=data, headers=expected_headers)

    def test_reports_a_bounce_if_it_is_a_bounce_and_does_not_post_to_the_api(self):
        f = open('mailit/tests/fixture/bounced_mail2.txt')
        bounce = f.readlines()
        f.close()
        self.answer = self.handler.handle(bounce)
        where_to_post_a_bounce = 'http://writeit.ciudadanointeligente.org/api/v1/handle_bounce/'
        config.WRITEIT_API_WHERE_TO_REPORT_A_BOUNCE = where_to_post_a_bounce
        self.assertEquals(self.answer.requests_session.auth.api_key, self.user.api_key.key)
        self.assertEquals(self.answer.requests_session.auth.username, self.user.username)
        expected_headers = {'content-type': 'application/json'}
        data = {'key': self.answer.outbound_message_identifier}
        data = json.dumps(data)

        with patch('requests.Session.post') as post:
            post.return_value = PostMock()

            self.answer.send_back()

            post.assert_called_with(where_to_post_a_bounce, data=data, headers=expected_headers)

    def test_logs_the_result_of_send_back(self):
        email_answer = EmailAnswer()
        email_answer.subject = 'prueba4'
        email_answer.content_text = 'prueba4lafieritaespeluda'
        email_answer.outbound_message_identifier = '8974aabsdsfierapulgosa'
        email_answer.email_from = 'falvarez@votainteligente.cl'
        email_answer.when = 'Wed Jun 26 21:05:33 2013'
        with patch('logging.info') as info:
            info.return_value = None
            with patch('requests.Session.post') as post:
                post.return_value = PostMock()

                with patch('logging.info') as info:
                    expected_log = "When sent to %(location)s the status code was 201" % {
                        'location': self.where_to_post_creation_of_the_answer
                        }
                    email_answer.send_back()
                    info.assert_called_with(expected_log)

    def test_logs_the_incoming_email(self):

        with patch('logging.info') as info:
            info.return_value = None

            self.answer = self.handler.handle(self.email)
            expected_log = 'New incoming email from %(from)s sent on %(date)s with subject %(subject)s and content %(content)s'
            expected_log = expected_log % {
                'from': self.answer.email_from,
                'date': self.answer.when,
                'subject': self.answer.subject,
                'content': self.answer.content_text,
                }
            info.assert_called_with(expected_log)

    def test_gets_the_message_id(self):
        '''The answer gets the message id'''
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.message_id, '<CAA5PczfGfdhf29wgK=8t6j7hm8HYsBy8Qg87iTU2pF42Ez3VcQ@mail.gmail.com>')

    def test_send_back_also_returns_an_answer(self):
        '''the method EmailAnswer.send_back returns an answer'''
        email_answer = EmailAnswer()
        email_answer.subject = 'prueba4'
        email_answer.content_text = 'prueba4lafieritaespeluda'
        email_answer.outbound_message_identifier = '8974aabsdsfierapulgosa'
        email_answer.email_from = 'falvarez@votainteligente.cl'
        email_answer.when = 'Wed Jun 26 21:05:33 2013'
        # so when I execute email_answer.save, it will return
        # the first answer that we have in our fixtures
        # it doesn't really matter as long as it returns an answer
        answer = Answer.objects.first()
        with patch('requests.Session.post') as post:
            post.return_value = PostMock()
            with patch('mailit.bin.handleemail.EmailAnswer.save') as save_answer:
                save_answer.return_value = answer
                result = email_answer.send_back()
                self.assertEquals(result, answer)


class HandleBounces(TestCase):
    def setUp(self):
        super(HandleBounces, self).setUp()
        self.user = User.objects.get(id=1)
        f = open('mailit/tests/fixture/bounced_mail2.txt')
        self.email = f.readlines()
        f.close()
        self.where_to_post_a_bounce = 'http://writeit.ciudadanointeligente.org//api/v1/handle_bounce/'
        config.WRITEIT_API_WHERE_TO_REPORT_A_BOUNCE = self.where_to_post_a_bounce
        config.WRITEIT_API_KEY = self.user.api_key.key
        config.WRITEIT_USERNAME = self.user.username
        self.handler = EmailHandler()

    def test_after_handling_the_message_is_set_to_bounced(self):
        self.answer = self.handler.handle(self.email)
        self.assertTrue(self.answer.is_bounced)

    def test_it_handles_the_bounces_and_pushes_the_identifier_key_to_the_api(self):
        self.answer = self.handler.handle(self.email)
        self.assertEquals(self.answer.requests_session.auth.api_key, self.user.api_key.key)
        self.assertEquals(self.answer.requests_session.auth.username, self.user.username)
        expected_headers = {'content-type': 'application/json'}
        data = {'key': self.answer.outbound_message_identifier}
        data = json.dumps(data)

        with patch('requests.Session.post') as post:
            post.return_value = PostMock()

            self.answer.report_bounce()

            post.assert_called_with(self.where_to_post_a_bounce, data=data, headers=expected_headers)

@override_settings(FLAG_BOUNCED_CONTACTS = True)
class BouncedMessageRecordTestCase(TestCase):
    def setUp(self):
        super(BouncedMessageRecordTestCase, self).setUp()
        self.outbound_message = OutboundMessage.objects.get(id=1)
        self.identifier = OutboundMessageIdentifier.objects.first()
        self.identifier.key = '4aaaabbb'
        self.identifier.save()
        self.bounced_email = ""
        with open('mailit/tests/fixture/bounced_mail2.txt') as f:
            self.bounced_email += f.read()
        f.close()
        self.bounced_email.replace(self.identifier.key, '')

        self.handler = EmailHandler(answer_class=OutboundMessageAnswer)

    def test_creation(self):
        bounced_message = BouncedMessageRecord.objects.create(
            outbound_message=self.outbound_message,
            bounce_text=self.bounced_email,
            )
        self.assertTrue(bounced_message)
        self.assertEquals(bounced_message.outbound_message, self.outbound_message)
        self.assertFalse(bounced_message.date is None)
        self.assertEquals(bounced_message.bounce_text, self.bounced_email)

    def test_it_creates_a_bounced_message_when_comes_a_new_bounce(self):
        email_answer = self.handler.handle(self.bounced_email)
        identifier = OutboundMessageIdentifier.objects.get(key=email_answer.outbound_message_identifier)
        outbound_message = OutboundMessage.objects.get(outboundmessageidentifier=identifier)
        email_answer.send_back()
        bounced_messages = BouncedMessageRecord.objects.filter(outbound_message=outbound_message)

        self.assertEquals(bounced_messages.count(), 1)
        bounced_message = bounced_messages[0]
        self.assertEquals(bounced_message.bounce_text, email_answer.content_text)


@override_settings(FLAG_BOUNCED_CONTACTS = True)
class BouncedMailInAmazonBug(TestCase):
    def setUp(self):
        super(BouncedMailInAmazonBug, self).setUp()
        self.message = Message.objects.get(id=1)
        self.contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.outbound_message = OutboundMessage.objects.create(message=self.message, contact=self.contact, site=Site.objects.get_current())
        identifier = OutboundMessageIdentifier.objects.get(outbound_message=self.outbound_message)
        identifier.key = "4aaaabbb"
        identifier.save()

        self.bounced_email = ""
        with open('mailit/tests/fixture/bounced_mail2.txt') as f:
            self.bounced_email += f.read()
        f.close()
        self.handler = EmailHandler(answer_class=OutboundMessageAnswer)
        self.answer = self.handler.handle(self.bounced_email)
        self.answer.send_back()

    def test_it_marks_the_contact_as_a_bounce(self):
        contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.assertTrue(contact.is_bounced)

    def test_it_marks_the_outbound_message_as_an_error(self):
        #I have to look for it again cause it has changed in the DB
        outbound_message = OutboundMessage.objects.get(id=self.outbound_message.id)
        self.assertEquals(outbound_message.status, "error")

class FlaggingBouncedMail(TestCase):
    def setUp(self):
        super(FlaggingBouncedMail, self).setUp()
        self.message = Message.objects.get(id=1)
        self.contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.outbound_message = OutboundMessage.objects.create(message=self.message, contact=self.contact, site=Site.objects.get_current())
        identifier = OutboundMessageIdentifier.objects.get(outbound_message=self.outbound_message)
        identifier.key = "4aaaabbb"
        identifier.save()

        self.bounced_email = ""
        with open('mailit/tests/fixture/bounced_mail2.txt') as f:
            self.bounced_email += f.read()
        f.close()
        self.handler = EmailHandler(answer_class=OutboundMessageAnswer)
        self.answer = self.handler.handle(self.bounced_email)
        self.answer.send_back()

    def test_it_does_not_mark_the_contact_as_bounced(self):
        contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.assertFalse(contact.is_bounced)

@override_settings(FLAG_BOUNCED_CONTACTS = True)
class FlaggingBouncedMailWriteItDefault(TestCase):

    def setUp(self):
        super(FlaggingBouncedMailWriteItDefault, self).setUp()
        self.message = Message.objects.get(id=1)
        self.contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.outbound_message = OutboundMessage.objects.create(message=self.message, contact=self.contact, site=Site.objects.get_current())
        identifier = OutboundMessageIdentifier.objects.get(outbound_message=self.outbound_message)
        identifier.key = "4aaaabbb"
        identifier.save()

        self.bounced_email = ""
        with open('mailit/tests/fixture/bounced_mail2.txt') as f:
            self.bounced_email += f.read()
        f.close()
        self.handler = EmailHandler(answer_class=OutboundMessageAnswer)
        self.answer = self.handler.handle(self.bounced_email)
        self.answer.send_back()

    def test_it_marks_the_contact_as_bounced_when_flag_bounced_contact_is_true(self):
        contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.assertTrue(contact.is_bounced)


@override_settings(FLAG_BOUNCED_CONTACTS = True)
class BouncedMailInGmail(TestCase):
    def setUp(self):
        super(BouncedMailInGmail, self).setUp()
        self.message = Message.objects.get(id=1)
        self.contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.outbound_message = OutboundMessage.objects.create(
            message=self.message, contact=self.contact, site=Site.objects.get_current())
        self.outbound_message.send()
        identifier = OutboundMessageIdentifier.objects.get(outbound_message=self.outbound_message)
        identifier.key = "4aaaabbb"
        identifier.save()

        self.bounced_email = ""
        with open('mailit/tests/fixture/bounced_mail.txt') as f:
            self.bounced_email += f.read()
        f.close()
        self.handler = EmailHandler(answer_class=OutboundMessageAnswer)
        self.answer = self.handler.handle(self.bounced_email)
        self.answer.send_back()

    def test_it_marks_the_contact_as_a_bounce(self):
        contact = Contact.objects.get(value="mailnoexistente@ciudadanointeligente.org")
        self.assertTrue(contact.is_bounced)

    def test_it_marks_the_outbound_message_as_an_error(self):
        #I have to look for it again cause it has changed in the DB
        outbound_message = OutboundMessage.objects.get(id=self.outbound_message.id)
        self.assertEquals(outbound_message.status, "error")

    def test_it_marks_the_outbound_record_to_try_again(self):
        record = OutboundMessagePluginRecord.objects.get(outbound_message=self.outbound_message)
        self.assertTrue(record.try_again)


class EmailReadingExamplesTestCase(TestCase):
    def setUp(self):
        super(EmailReadingExamplesTestCase, self).setUp()
        self.message = Message.objects.get(id=1)
        self.contact = Contact.objects.get(value="falvarez@ciudadanointeligente.cl")
        self.outbound_message = OutboundMessage.objects.create(message=self.message, contact=self.contact, site=Site.objects.get_current())
        self.outbound_message.send()
        identifier = OutboundMessageIdentifier.objects.get(outbound_message=self.outbound_message)
        identifier.key = "7e460e9c462411e38ef81231400178dd"
        identifier.save()
        self.handler = EmailHandler()

    def test_example1_gmail(self):
        f = open('mailit/tests/fixture/example1_gmail.txt')
        email = f.readlines()
        f.close()

        answer = self.handler.handle(email)
        self.assertEquals(answer.content_text, u"si prueba no más")
        self.assertIn(u"si prueba no más", answer.content_html)

    @skip("this fails because it still has some parts from the origina email, probably this is not easy taken away")
    def test_example2_gmail(self):
        f = open('mailit/tests/fixture/example2_gmail.txt')
        email = f.readlines()
        f.close()

        answer = self.handler.handle(email)
        self.assertEquals(answer.content_text, u"de nuevo de nuevo")

    def test_example3_ipad(self):
        f = open('mailit/tests/fixture/example3_ipad.txt')
        email = f.readlines()
        f.close()

        answer = self.handler.handle(email)
        self.assertEquals(answer.content_text, u"Primero que todo los felicito por la iniciativa , ojalá lleguen más preguntas .")

    def test_example4_hotmail(self):
        f = open('mailit/tests/fixture/example4_hotmail.txt')
        email = f.readlines()
        f.close()

        answer = self.handler.handle(email)
        self.assertIn(u"chilen@ está ausente más de 10 horas de su hogar despreocup", answer.content_text)

    def test_example5_michellebachelet(self):
        f = open('mailit/tests/fixture/example5_michellebachelet.txt')
        email = f.readlines()
        f.close()

        answer = self.handler.handle(email)
        self.assertIn(u"Realizaremos un proceso de consulta con los Pueblos", answer.content_text)
