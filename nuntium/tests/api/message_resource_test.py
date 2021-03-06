# -*- coding: utf-8 -*-
from django.core.management import call_command
from instance.models import PopoloPerson, WriteItInstance
from ...models import Message, Confirmation
from tastypie.test import ResourceTestCase, TestApiClient
from django.contrib.auth.models import User
from django.utils.encoding import force_text


class MessageResourceTestCase(ResourceTestCase):
    def setUp(self):
        super(MessageResourceTestCase, self).setUp()
        call_command('loaddata', 'example_data', verbosity=0)
        self.user = User.objects.get(id=1)
        self.writeitinstance = WriteItInstance.objects.create(name=u"a test", slug=u"a-test", owner=self.user)
        self.api_client = TestApiClient()
        self.data = {'format': 'json', 'username': self.user.username, 'api_key': self.user.api_key.key}

    def get_credentials(self):
        credentials = self.create_apikey(username=self.user.username, api_key=self.user.api_key.key)
        return credentials

    def test_get_list_of_messages(self):
        url = '/api/v1/message/'
        with self.assertNumQueries(11):
            response = self.api_client.get(url, data=self.data)

        self.assertValidJSONResponse(response)

        messages = self.deserialize(response)['objects']
        # Only listing my messages
        expected_messages = Message.public_objects.filter(writeitinstance__in=self.user.writeitinstances.all())
        self.assertEqual(len(messages), expected_messages.count())  # Only my instances
        first_message = messages[0]
        self.assertNotIn('author_email', first_message.keys())

    def test_only_listing_my_messages(self):
        not_me = User.objects.create_user(username='not_me', password='not_my_password')
        writeitinstance = WriteItInstance.objects.create(name=u"a test", slug=u"a-test", owner=not_me)
        person1 = PopoloPerson.objects.get(id=1)
        writeitinstance.add_person(person1)
        i_should_not_see_this_message = Message.objects.create(
            content='Content 1 Public message',
            author_name='Felipe',
            author_email="falvarez@votainteligente.cl",
            subject='Fiera es una perra feroz',
            writeitinstance=writeitinstance,
            persons=[person1],
            )
        Confirmation.objects.create(message=i_should_not_see_this_message)
        i_should_not_see_this_message.recently_confirmated()
        self.assertTrue(i_should_not_see_this_message.public)
        expected_messages = Message.public_objects.filter(writeitinstance__in=self.user.writeitinstances.all())
        self.assertNotIn(i_should_not_see_this_message, expected_messages)
        self.assertIn(i_should_not_see_this_message, Message.public_objects.all())
        url = '/api/v1/message/'
        response = self.api_client.get(url, data=self.data)

        self.assertValidJSONResponse(response)

        messages = self.deserialize(response)['objects']
        i_should_not_see_this_message_as_json = None
        # Seriously, this can be done in a more elegant way
        # I'll keep on working with this and I'll return to this test
        # later
        for message in messages:
            if message['id'] == i_should_not_see_this_message.id:
                i_should_not_see_this_message_as_json = message
        self.assertIsNone(i_should_not_see_this_message_as_json)

        # The detail of a message
        url = '/api/v1/message/{0}/'.format(i_should_not_see_this_message.id)
        response = self.api_client.get(url, data=self.data)
        self.assertHttpUnauthorized(response)

    def test_list_of_messages_is_ordered(self):
        """ The list of messages shown in the API is ordered by created date"""
        # Preparing the test
        Message.objects.all().delete()
        person1 = PopoloPerson.objects.get(id=1)
        # cleaning up the database before
        message1 = Message.objects.create(
            content=u'Content 1',
            author_name=u'Felipe',
            author_email=u"falvarez@votainteligente.cl",
            subject=u'Fiera es una perra feroz 1',
            writeitinstance=self.writeitinstance,
            persons=[person1],
            )
        Confirmation.objects.create(message=message1)
        message1.recently_confirmated()

        message2 = Message.objects.create(
            content=u'Content 2',
            author_name=u'Felipe',
            author_email=u"falvarez@votainteligente.cl",
            subject=u'Fiera es una perra feroz 2',
            writeitinstance=self.writeitinstance,
            persons=[person1],
            )
        Confirmation.objects.create(message=message2)
        message2.recently_confirmated()

        url = '/api/v1/message/'
        response = self.api_client.get(url, data=self.data)

        self.assertValidJSONResponse(response)

        messages = self.deserialize(response)['objects']
        self.assertEquals(messages[0]['id'], message2.id)
        self.assertEquals(messages[1]['id'], message1.id)

    def test_authentication(self):
        url = '/api/v1/message/'
        response = self.api_client.get(url)

        self.assertHttpUnauthorized(response)

    def test_a_list_of_messages_have_answers(self):
        url = '/api/v1/message/'
        response = self.api_client.get(url, data=self.data)
        self.assertValidJSONResponse(response)
        messages = self.deserialize(response)['objects']

        self.assertTrue('answers' in messages[0])

    def test_the_message_has_the_persons_it_was_sent_to(self):
        url = '/api/v1/message/'
        response = self.api_client.get(url, data=self.data)
        self.assertValidJSONResponse(response)
        messages = self.deserialize(response)['objects']

        self.assertTrue('persons' in messages[0])
        message_from_the_api = messages[0]
        message = Message.objects.get(id=messages[0]['id'])
        for person_uri in message_from_the_api['persons']:
            self.assertIn(
                PopoloPerson.objects.get(identifiers__identifier=person_uri),
                message.people.all(),
            )

    def test_create_a_new_message(self):
        writeitinstance = WriteItInstance.objects.get(id=1)
        message_data = {
            'author_name': 'Felipipoo',
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': [writeitinstance.persons.all()[0].old_popit_url],
        }

        url = '/api/v1/message/'
        previous_amount_of_messages = Message.objects.count()
        response = self.api_client.post(url, data=message_data, format='json', authentication=self.get_credentials())
        self.assertHttpCreated(response)
        self.assertValidJSON(force_text(response.content))
        message_as_json = force_text(response.content)
        self.assertIn('resource_uri', message_as_json)

        post_amount_of_messages = Message.objects.count()
        self.assertEquals(post_amount_of_messages, previous_amount_of_messages + 1)

        the_message = Message.objects.get(author_name='Felipipoo')

        outbound_messages = the_message.outboundmessage_set.all()
        self.assertTrue(outbound_messages.count() > 0)
        for outbound_message in outbound_messages:
            self.assertEquals(outbound_message.status, 'ready')

    def test_create_a_new_message_in_not_my_instance(self):
        not_me = User.objects.create_user(username='not_me', password='not_my_password')
        writeitinstance = WriteItInstance.objects.create(name=u"a test", slug=u"a-test", owner=not_me)
        person1 = PopoloPerson.objects.get(id=1)
        writeitinstance.add_person(person1)
        message_data = {
            'author_name': 'Felipipoo',
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': [person1.old_popit_url],
        }

        url = '/api/v1/message/'
        response = self.api_client.post(url, data=message_data, format='json', authentication=self.get_credentials())
        self.assertHttpUnauthorized(response)

    def test_create_a_new_message_with_a_non_existing_person(self):
        writeitinstance = WriteItInstance.objects.get(id=1)
        message_data = {
            'author_name': 'Felipipoo',
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': [
                writeitinstance.persons.all()[0].old_popit_url,
                'http://this.person.does.not.exist',
                ],
        }
        url = '/api/v1/message/'
        response = self.api_client.post(url, data=message_data, format='json', authentication=self.get_credentials())
        self.assertHttpCreated(response)
        the_message = Message.objects.get(author_name='Felipipoo')
        outbound_messages = the_message.outboundmessage_set.all()
        self.assertEquals(outbound_messages.count(), 1)
        self.assertEquals(outbound_messages[0].contact.person, writeitinstance.persons.all()[0])

    def test_create_a_new_message_confirmated(self):
        writeitinstance = WriteItInstance.objects.get(id=1)
        message_data = {
            'author_name': 'Felipipoo',
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': [writeitinstance.persons.all()[0].old_popit_url],
        }
        url = '/api/v1/message/'
        self.api_client.post(url, data=message_data, format='json', authentication=self.get_credentials())

        the_message = Message.objects.get(author_name='Felipipoo')

        self.assertTrue(the_message.confirmated)

    def test_create_a_new_message_to_all_persons_in_the_instance(self):
        # here it is the thing I don't know yet how to do this and I'll go for
        # saying all in the persons array instead of having an array or an empty
        writeitinstance = WriteItInstance.objects.get(id=1)
        message_data = {
            'author_name': 'Felipipoo',
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': "all",
        }
        url = '/api/v1/message/'
        self.api_client.post(url, data=message_data, format='json', authentication=self.get_credentials())

        the_message = Message.objects.get(author_name=u'Felipipoo')

        self.assertEquals(len(the_message.people), writeitinstance.persons.count())
        self.assertQuerysetEqual(
            the_message.people.all(),
            [repr(r) for r in writeitinstance.persons.all()]
            )

    def test_not_confirming_automatically_a_message(self):
        """Push a new message to an instance with no autoconfirm message"""
        writeitinstance = WriteItInstance.objects.get(id=1)
        writeitinstance.config.autoconfirm_api_messages = False
        writeitinstance.config.save()

        message_data = {
            'author_name': 'Felipipoo',
            'author_email': "falvarez@votainteligente.cl",
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': "all",
        }
        url = '/api/v1/message/'
        self.api_client.post(
            url,
            data=message_data,
            format='json',
            authentication=self.get_credentials(),
            )

        the_message = Message.objects.get(author_name='Felipipoo')

        self.assertFalse(the_message.confirmated)
        self.assertIsNotNone(the_message.confirmation)

    def test_not_including_email_in_non_auto_confrim_message(self):
        """Not Including email causes error 403 in a non auto confirm message"""
        writeitinstance = WriteItInstance.objects.get(id=1)
        writeitinstance.config.autoconfirm_api_messages = False
        writeitinstance.config.save()

        message_data = {
            'author_name': 'Felipipoo',
            # 'author_email': "falvarez@votainteligente.cl", # this missing param will cause a 403
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': "all",
        }
        url = '/api/v1/message/'
        response = self.api_client.post(
            url,
            data=message_data,
            format='json',
            authentication=self.get_credentials(),
            )

        self.assertEquals(response.status_code, 400)
        self.assertFalse(Message.objects.filter(author_name='Felipipoo'))

    def test_including_a_non_email_in_the_author_email(self):
        """When it has an author_email it validates it"""
        writeitinstance = WriteItInstance.objects.get(id=1)

        message_data = {
            'author_name': 'Felipipoo',
            'author_email': "This is not an email",  # this missing param will cause a 403
            'subject': 'new message',
            'content': 'the content thing',
            'writeitinstance': '/api/v1/instance/{0}/'.format(writeitinstance.id),
            'persons': "all"
        }
        url = '/api/v1/message/'
        response = self.api_client.post(
            url,
            data=message_data,
            format='json',
            authentication=self.get_credentials(),
            )

        self.assertEquals(response.status_code, 400)
        self.assertFalse(Message.objects.filter(author_name='Felipipoo'))

    def test_get_list_of_messages_filtered_by_popolo_uri(self):
        popolo_uri = 'http://example.com/popolo.json#person-123'
        # Create a person with a popolo identifier
        person = PopoloPerson.objects.create(name='Test')
        person.identifiers.create(scheme='popolo_uri', identifier=popolo_uri)
        # Create an extra message that we don't expect to see in the response
        message = Message.objects.create(
            content=u'Test Content',
            author_name=u'Felipe',
            author_email=u"falvarez@votainteligente.cl",
            subject=u'Fiera es una perra feroz',
            writeitinstance=self.writeitinstance,
            persons=[person],
            )
        message.recently_confirmated()

        # Fetch a filtered list of message from the API
        url = '/api/v1/message/'
        params = self.data.copy()
        params.update({'person__popolo_uri': popolo_uri})
        response = self.api_client.get(url, data=params)
        self.assertValidJSONResponse(response)

        expected_message = Message.public_objects.get(writeitinstance__in=self.user.writeitinstances.all(), person=person)
        messages_from_api = self.deserialize(response)['objects']
        self.assertEqual(len(messages_from_api), 1)
        message_from_api = messages_from_api[0]
        self.assertEqual(message_from_api['id'], expected_message.id)
