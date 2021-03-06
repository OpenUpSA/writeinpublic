# -*- coding: utf-8 -*-
from django.core.management import call_command
from tastypie.test import ResourceTestCase, TestApiClient
from django.contrib.auth.models import User
from django.db.models import Count
from popolo.models import Identifier
from instance.models import PopoloPerson as Person


class PersonResourceTestCase(ResourceTestCase):
    def setUp(self):
        super(PersonResourceTestCase, self).setUp()
        call_command("loaddata", "example_data", verbosity=0)
        self.user = User.objects.get(id=1)
        self.api_client = TestApiClient()

        self.data = {
            "format": "json",
            "username": self.user.username,
            "api_key": self.user.api_key.key,
        }

    def get_credentials(self):
        credentials = self.create_apikey(
            username=self.user.username, api_key=self.user.api_key.key
        )
        return credentials

    def test_get_list_of_persons(self):
        url = "/api/v1/person/"
        response = self.api_client.get(url, authentication=self.get_credentials())

        self.assertValidJSONResponse(response)

        persons = self.deserialize(response)["objects"]
        self.assertEqual(len(persons), Person.objects.count())  # All the instances

    def test_unauthorized_list_of_persons(self):
        url = "/api/v1/person/"
        response = self.api_client.get(url)

        self.assertHttpUnauthorized(response)

    def test_the_remote_url_of_the_person_points_to_its_popit_instance(self):
        url = "/api/v1/person/"
        response = self.api_client.get(url, authentication=self.get_credentials())
        persons = self.deserialize(response)["objects"]
        self.assertEquals(persons[0]["popit_url"], persons[0]["resource_uri"])

    def test_filter_list_of_persons_by_identifier(self):
        id_count = Count("identifiers")
        person = (
            Person.objects.annotate(id_count=id_count).filter(id_count__gte=1).first()
        )
        identifier = person.identifiers.first()

        url = "/api/v1/person/?identifiers__identifier=%s&identifiers__scheme=%s" % (
            identifier.identifier,
            identifier.scheme,
        )
        response = self.api_client.get(url, authentication=self.get_credentials())

        self.assertValidJSONResponse(response)

        persons = self.deserialize(response)["objects"]
        self.assertEqual(1, len(persons))
        self.assertEqual(person.id, persons[0]["id"])

    def test_filter_list_of_persons_by_has_contacts(self):
        url = "/api/v1/person/?has_contacts=True"
        response = self.api_client.get(url, authentication=self.get_credentials())

        self.assertValidJSONResponse(response)

        persons = self.deserialize(response)["objects"]
        self.assertEqual(len(persons), 3)

    def test_filter_list_of_persons_by_does_not_have_contacts(self):
        url = "/api/v1/person/?has_contacts=False"
        response = self.api_client.get(url, authentication=self.get_credentials())

        self.assertValidJSONResponse(response)

        persons = self.deserialize(response)["objects"]
        self.assertEqual(len(persons), 1)

    def test_filter_invalid_has_contacts_value(self):
        url = "/api/v1/person/?has_contacts=something-else"
        response = self.api_client.get(url, authentication=self.get_credentials())

        self.assertHttpBadRequest(response)

    def test_filter_list_of_persons_by_instance(self):
        url = "/api/v1/person/?instance_id=%d" % 1
        response = self.api_client.get(url, authentication=self.get_credentials())

        self.assertValidJSONResponse(response)

        persons = self.deserialize(response)["objects"]
        self.assertEqual(len(persons), 1)
