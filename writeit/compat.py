# Compatibility shim for django-plugins which imports django.utils.six
# (removed in Django 3.0). This must be imported before djangoplugins.
import django.utils
import six
django.utils.six = six
