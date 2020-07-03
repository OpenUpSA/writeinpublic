from global_test_case import GlobalTestCase as TestCase
from nuntium.models import OutboundMessage, Answer
from django.core import mail
from django.test.utils import override_settings
from django.test import Client
from mailit.models import RawIncomingEmail
from mailit.exceptions import TemporaryFailure
from nuntium.models import OutboundMessageIdentifier
from mock import patch


def read_file(file_name):
    with open(file_name) as f:
        return f.read()


class IncomingMailTestCase(TestCase):
    def setUp(self):
        super(IncomingMailTestCase, self).setUp()
        self.outbound_message = OutboundMessage.objects.get(id=1)

    def test_webhook_post(self):
        identifier = self.outbound_message.outboundmessageidentifier
        identifier.key = '4aaaabbb'
        identifier.save()

        data = {'email': read_file('mailit/tests/fixture/mail.txt')}
        response = Client().post('/mailit/inbound/sendgrid/raw/', data=data)
        self.assertEqual(response.status_code, 200)

        the_answers = Answer.objects.filter(message=identifier.outbound_message.message)
        self.assertEquals(the_answers.count(), 1)
        self.assertEquals(the_answers[0].content, 'prueba4lafieri')

    def test_webhook_post_does_not_include_identifier_in_content(self):
        identifier = self.outbound_message.outboundmessageidentifier
        identifier.key = '4aaaabbb'
        identifier.save()

        data = {'email': read_file('mailit/tests/fixture/mail_with_identifier_in_the_content.txt')}
        response = Client().post('/mailit/inbound/sendgrid/raw/', data=data)
        self.assertEqual(response.status_code, 200)

        the_answers = Answer.objects.filter(message=identifier.outbound_message.message)
        self.assertEquals(the_answers.count(), 1)
        self.assertFalse(identifier.key in the_answers[0].content)

    @override_settings(ADMINS=(('Felipe', 'falvarez@admins.org'),))
    def test_it_sends_an_email_to_the_admin_if_any_failure(self):

        data = {'email': read_file('mailit/tests/fixture/mail_for_no_message.txt')}
        response = Client().post('/mailit/inbound/sendgrid/raw/', data=data)
        self.assertEqual(response.status_code, 200)

        # Admins don't get an email
        self.assertEquals(len(mail.outbox), 0)
        # but the email gets registered
        identifier = '<CAA5PczfGfdhf29wgK=8t6j7hm8HYsBy8Qg87iTU2pF42Ez3VcQ@mail.gmail.com>'
        self.assertTrue(RawIncomingEmail.objects.filter(content__contains=identifier))

    @override_settings(ADMINS=(('Felipe', 'falvarez@admins.org'),))
    def test_mail_admins_if_theres_a_problem(self):
        killer_mail_mime = 'this should kill the parser!'
        data = {'email': killer_mail_mime}
        with self.assertRaises(Exception):
            Client().post('/mailit/inbound/sendgrid/raw/', data=data)

        self.assertEquals(len(mail.outbox), 1)
        self.assertNotIn(killer_mail_mime, mail.outbox[0].body)
        self.assertEquals(mail.outbox[0].to[0], 'falvarez@admins.org')
        self.assertEquals(len(mail.outbox[0].attachments), 1)

    def test_it_correctly_parses_the_to_email(self):
        '''As described in #773 emails can contain odd parts'''
        identifier = self.outbound_message.outboundmessageidentifier
        identifier.key = '4aaaabbb'
        identifier.save()

        data = {'email': read_file('mailit/tests/fixture/mail_from_tony.txt')}
        response = Client().post('/mailit/inbound/sendgrid/raw/', data=data)
        self.assertEqual(response.status_code, 200)

        the_answer = Answer.objects.get(message=identifier.outbound_message.message)
        self.assertNotIn('Tony', the_answer.content)
        self.assertNotIn('<eduskunta-', the_answer.content)
        self.assertNotIn('>', the_answer.content)

    def test_temporary_failure_raises_temp_fail_error(self):
        data = {'email': read_file('mailit/tests/fixture/temporary.txt')}
        with self.assertRaises(TemporaryFailure):
            Client().post('/mailit/inbound/sendgrid/raw/', data=data)

    @patch('mailit.views.logger')
    @override_settings(ADMINS=(('Felipe', 'falvarez@admins.org'),))
    def test_mail_admins_if_outbound_message_identifier_error(self, logger_patch):
        # Make sure there are no OutboundMessageIdentifiers with this key
        key = '4aaaabbb'
        OutboundMessageIdentifier.objects.filter(key=key).all().delete()

        # Should not raise error
        data = {'email': read_file('mailit/tests/fixture/mail_from_tony.txt')}
        response = Client().post('/mailit/inbound/sendgrid/raw/', data=data)
        self.assertEqual(response.status_code, 200)

        # Should mail admins
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to[0], 'falvarez@admins.org')
        self.assertEquals(len(mail.outbox[0].attachments), 1)

        # Should log the error
        args = logger_patch.error.call_args[0][0]
        self.assertEquals('OutboundMessageIdentifier matching query does not exist.', str(args))
