# coding=utf-8
from .models import Message, Answer


def message_search_queryset():
    return Message.public_objects.all()


def answer_search_queryset():
    return Answer.objects.filter(message__in=Message.public_objects.all())
