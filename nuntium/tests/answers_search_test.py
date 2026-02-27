# coding=utf-8
from global_test_case import GlobalTestCase as TestCase, SearchIndexTestCase
from ..search_indexes import answer_search_queryset
from subdomains.utils import reverse
from ..models import Answer, Message
import urllib
import urlparse


class AnswerSearchQuerysetTestCase(TestCase):
    def setUp(self):
        super(AnswerSearchQuerysetTestCase, self).setUp()
        for message in Message.objects.all():
            message.confirmated = True
            message.save()

    def test_public_answers_are_searchable(self):
        public_answers = Answer.objects.filter(message__in=Message.public_objects.all())
        qs = answer_search_queryset()
        for answer in public_answers:
            self.assertIn(answer, qs)

    def test_private_message_answers_not_searchable(self):
        private_message_answers = Answer.objects.exclude(message__in=Message.public_objects.all())
        qs = answer_search_queryset()
        for answer in private_message_answers:
            self.assertNotIn(answer, qs)


class SearchAnswerAccess(SearchIndexTestCase):
    def setUp(self):
        super(SearchAnswerAccess, self).setUp()
        for message in Message.objects.all():
            message.confirmated = True
            message.save()

    def test_access_the_url(self):
        url = reverse('search_messages', subdomain=None)
        url += "/"
        params = {'q': 'Public Answer'}

        url_parts = list(urlparse.urlparse(url))
        url_parts[4] = urllib.urlencode(params)
        url_with_parameters = urlparse.urlunparse(url_parts)
        response = self.client.get(url_with_parameters)
        self.assertEquals(response.status_code, 200)

        self.assertIn('page', response.context)
        results = response.context['page'].object_list

        self.assertGreaterEqual(len(results), 1)
