# -*- coding: utf-8 -*-

import json

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, ALL, Resource
from instance.models import PopoloPerson, WriteItInstance
from popolo.models import Identifier
from .models import Message, Answer, \
    OutboundMessageIdentifier, OutboundMessage, Confirmation, NoContactOM
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from django.core.exceptions import ObjectDoesNotExist
from django.conf.urls import url
from tastypie import fields
from tastypie.exceptions import ImmediateHttpResponse, InvalidFilterError
from tastypie import http
from contactos.models import Contact
from django.db.models import Prefetch
from tastypie.paginator import Paginator
from django.http import Http404, HttpResponseBadRequest
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from tastypie.bundle import Bundle
from tastypie.exceptions import Unauthorized


class PagePaginator(Paginator):
    def get_offset(self):
        if 'page' in self.request_data:
            return self.get_offset_from_page()
        return super(PagePaginator, self).get_offset()

    def get_offset_from_page(self):
        page = int(self.request_data.get('page'))
        offset = (page - 1) * self.get_limit()
        return offset


class IdentifierResource(ModelResource):
    class Meta:
        queryset = Identifier.objects.all()
        resource_name = 'identifier'
        filtering = {
            'identifier': ALL,
            'scheme': ALL,
        }
        allowed_methods = []

class PersonResource(ModelResource):
    identifiers = fields.ToManyField(IdentifierResource, 'identifiers', full=True)

    class Meta:
        queryset = PopoloPerson.objects.all().prefetch_related('identifiers')
        resource_name = 'person'
        authentication = ApiKeyAuthentication()
        filtering = {
            'identifiers': ALL_WITH_RELATIONS,
        }

    # def get_object_list(self, request):
    #     queryset = super(PersonResource, self).get_object_list()
    #     return queryset.prefetch_related('identifiers')

    def obj_get_list(self, bundle, **kwargs):
        result = super(PersonResource, self).obj_get_list(bundle, **kwargs)

        filters = bundle.request.GET.copy()
        if 'has_contacts' in filters:
            # Count the number of contacts the person has
            filters['has_contacts'] = filters['has_contacts'].lower()
            if filters['has_contacts'] == 'true':
                result = result.has_contacts()
            elif filters['has_contacts'] == 'false':
                result = result.doesnt_have_contacts()
            else:
                raise InvalidFilterError("'has_contacts' field must either be 'true' or 'false'.")

        if 'instance_id' in filters:
            result = result.filter(writeit_instances__id=filters['instance_id'])

        return result


    def dehydrate(self, bundle):
        bundle.data['resource_uri'] = bundle.obj.uri_for_api()
        bundle.data['popit_id'] = bundle.obj.old_popit_id
        bundle.data['popit_url'] = bundle.obj.uri_for_api()
        return bundle


class WriteItInstanceResource(ModelResource):
    # I should add persons but the thing is that
    # it breaks some other tests and I'm running out of time
    # so now you cannot create a writeit instance with persons
    # just with a popit-instance =)
    # regards the lazy programmer
    class Meta:
        queryset = WriteItInstance.objects.all()
        resource_name = 'instance'
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        always_return_data = True
        filtering = {'id': 'exact'}

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<id>[-\d]+)/messages/$" % self._meta.resource_name,
                self.wrap_view('handle_instance_messages'),
                name="api_handle_messages"),
            url(
                r"^(?P<resource_name>%s)/(?P<id>[-\d]+)/answers/$" % self._meta.resource_name,
                self.wrap_view('handle_instance_answers'),
                name="api_handle_messages"),
            ]

    def handle_instance_messages(self, request, *args, **kwargs):
        self.is_authenticated(request)
        basic_bundle = self.build_bundle(request=request)
        obj = self.cached_obj_get(
            bundle=basic_bundle,
            **self.remove_api_resource_names(kwargs)
            )
        return MessageResource().get_list(request, writeitinstance=obj)

    def handle_instance_answers(self, request, *args, **kwargs):
        basic_bundle = self.build_bundle(request=request)
        obj = self.cached_obj_get(bundle=basic_bundle,
                                  **self.remove_api_resource_names(kwargs))
        return AnswerResource().get_list(request, writeitinstance=obj)

    def dehydrate(self, bundle):
        # not completely sure that this is the right way to get the messages
        bundle.data['messages_uri'] = bundle.data['resource_uri'] + 'messages/'
        self.add_persons_to_bundle(bundle)
        return bundle

    def add_persons_to_bundle(self, bundle):
        bundle.data['persons'] = []
        for person in bundle.obj.persons.all():
            bundle.data['persons'].append(person.uri_for_api())
        return bundle

    def hydrate(self, bundle):
        bundle.obj.owner = bundle.request.user
        return bundle

    def obj_create(self, bundle):
        bundle = super(WriteItInstanceResource, self).obj_create(bundle)
        instance = bundle.obj
        if "popit-api" in bundle.data and bundle.data["popit-api"]:
            instance.load_persons_from_popolo_json(bundle.data["popit-api"])
        return bundle


class AnswerResource(ModelResource):
    person = fields.ToOneField(
        PersonResource,
        'person',
        full=True,
        null=True,
        )

    class Meta:
        queryset = Answer.objects.all().select_related('person').order_by('-created')
        resource_name = 'answer'

    def get_list(self, request, **kwargs):
        self.writeitinstance = None
        if "writeitinstance" in kwargs:
            self.writeitinstance = kwargs.pop("writeitinstance")
        return super(AnswerResource, self).get_list(request, **kwargs)

    def apply_filters(self, request, applicable_filters):
        result = super(AnswerResource, self).apply_filters(request, applicable_filters)
        if self.writeitinstance:
            result = result.filter(message__writeitinstance=self.writeitinstance)
        return result

    def dehydrate(self, bundle):
        bundle.data['message_id'] = bundle.obj.message.id
        return bundle


class MessageAuthorization(Authorization):
    def read_detail(self, object_list, bundle):
        return bundle.obj.writeitinstance.owner == bundle.request.user

    def read_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized('Not Authorized')
        return object_list.filter(writeitinstance__in=bundle.request.user.writeitinstances.all())

    def create_list(self, object_list, bundle):
        raise Unauthorized('Not Authorized')

    def create_detail(self, object_list, bundle):
        writeitinstance = WriteItInstanceResource().get_via_uri(
            bundle.data["writeitinstance"]
            )
        if writeitinstance.owner != bundle.request.user:
            raise Unauthorized('Not Authorized')
        return super(MessageAuthorization, self).create_detail(object_list, bundle)


class MessageResource(ModelResource):
    writeitinstance = fields.ToOneField(WriteItInstanceResource,
                                        'writeitinstance')
    answers = fields.ToManyField(AnswerResource, 'answers',
                                 null=True,
                                 full=True)
    people = fields.ToManyField(PersonResource, 'people',
                                null=True,
                                readonly=True,
                                full=True)

    class Meta:
        # queryset = Message.public_objects.all().order_by('-created')
        queryset = Message.public_objects.select_related('writeitinstance')\
            .prefetch_related('answers__person__identifiers')\
            .prefetch_related(
                Prefetch(
                    'outboundmessage_set',
                    queryset=OutboundMessage.objects.select_related('contact__person')\
                        .prefetch_related('contact__person__identifiers').all()
                )) \
            .prefetch_related('outboundmessage_set__contact__person__identifiers')\
            .prefetch_related(
                Prefetch(
                    'nocontactom_set', 
                    queryset=NoContactOM.objects.select_related('person').\
                        prefetch_related('person__identifiers').all()
                )
            ) \
            .prefetch_related('nocontactom_set__person__identifiers')\
            .all().order_by('-created')
        # About the ordering
        # ordering = ['-created']
        # should work but it doesn't so I put it in the queryset
        resource_name = 'message'
        authorization = MessageAuthorization()
        authentication = ApiKeyAuthentication()
        always_return_data = True
        paginator_class = PagePaginator
        filtering = {
            'writeitinstance': ALL_WITH_RELATIONS
        }

    def build_filters(self, filters=None, ignore_bad_filters=False):
        result = super(MessageResource, self).build_filters(filters, ignore_bad_filters)
        queryset = PopoloPerson.objects.all()
        if 'writeitinstance__exact' in result:
            queryset = result['writeitinstance__exact'].persons.all()
        person = None
        if 'person' in filters:
            try:
                person = queryset.get(id=filters['person'])
            except:
                raise Http404("PopoloPerson does not exist")
        if 'person__popit_id' in filters:
            try:
                person = queryset.get(
                    identifiers__scheme='popit_id',
                    identifiers__identifier=filters['person__popit_id'],
                )
            except ObjectDoesNotExist:
                raise Http404("PopoloPerson does not exist")
        if 'person__popolo_uri' in filters:
            try:
                person = queryset.get(
                    identifiers__scheme='popolo_uri',
                    identifiers__identifier=filters['person__popolo_uri'],
                )
            except ObjectDoesNotExist:
                raise Http404("PopoloPerson does not exist")
        if person:
            result['person'] = person
        return result

    def hydrate(self, bundle):
        persons = []
        instance = WriteItInstanceResource().get_via_uri(
            bundle.data["writeitinstance"]
            )
        if not instance.config.autoconfirm_api_messages:
            if 'author_email' not in bundle.data:
                raise ImmediateHttpResponse(response=HttpResponseBadRequest("The author has no email"))
        if 'author_email' in bundle.data:
            # Validating author_email
            try:
                validate_email(bundle.data['author_email'])
            except ValidationError, e:
                raise ImmediateHttpResponse(response=HttpResponseBadRequest(e.__str__()))

        if bundle.data['persons'] == 'all':
            for person in instance.persons.all():
                persons.append(person)
        else:
            for person_api_url in bundle.data['persons']:
                try:
                    person = PopoloPerson.objects.get_from_api_uri(person_api_url)
                    persons.append(person)
                except ObjectDoesNotExist:
                    pass
        bundle.obj.persons = persons
        bundle.obj.confirmated = True
        return bundle

    def dehydrate(self, bundle):
        bundle.data['persons'] = []
        if 'author_email' in bundle.data:
            bundle.data.pop('author_email', None)
        for person in bundle.obj.people:
            print('\nfor person\n')
            bundle.data['persons'].append(person.uri_for_api())
        return bundle

    def obj_create(self, bundle, **kwargs):
        bundle = super(MessageResource, self).obj_create(bundle, **kwargs)
        if bundle.obj.writeitinstance.config.autoconfirm_api_messages:
            bundle.obj.recently_confirmated()
        else:
            bundle.obj.confirmated = False
            bundle.obj.save()
            Confirmation.objects.create(message=bundle.obj)
        return bundle


class AnswerCreationResource(Resource):
    class Meta:
        resource_name = 'create_answer'
        object_class = Answer
        authentication = ApiKeyAuthentication()
        allowed_methods = ['post', ]
        always_return_data = True

    def obj_create(self, bundle, **kwargs):
        identifier_key = bundle.data['key']
        identifier = OutboundMessageIdentifier.objects.get(key=bundle.data['key'])
        owner = identifier.outbound_message.message.writeitinstance.owner

        if owner != bundle.request.user:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        answer_content = bundle.data['content']
        answer = OutboundMessageIdentifier.create_answer(identifier_key, answer_content)
        bundle.obj = answer
        bundle.data['id'] = bundle.obj.id
        return bundle

    def detail_uri_kwargs(self, bundle_or_obj=None):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs[self._meta.detail_uri_name] = getattr(bundle_or_obj.obj, self._meta.detail_uri_name)
        else:
            kwargs[self._meta.detail_uri_name] = getattr(bundle_or_obj, self._meta.detail_uri_name)
        return kwargs


class HandleBouncesResource(Resource):
    class Meta:
        resource_name = 'handle_bounce'
        object_class = Contact
        authentication = ApiKeyAuthentication()
        allowed_methods = ['post', ]

    def obj_create(self, bundle, **kwargs):
        identifier_key = bundle.data['key']
        identifier = OutboundMessageIdentifier.objects.get(key=identifier_key)
        outbound_message = OutboundMessage.objects.get(
            outboundmessageidentifier=identifier
            )
        contact = outbound_message.contact
        contact.is_bounced = True
        contact.save()
