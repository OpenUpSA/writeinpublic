# Compatibility shim for django-plugins which imports modules
import django.utils
import django.utils.encoding
import django.conf.urls
import django.core.management.base
import six
django.utils.six = six

django.utils.encoding.python_2_unicode_compatible = lambda cls: cls

def _compat_patterns(prefix, *args):
    if prefix:
        raise Exception("Using a prefix with patterns() is not supported.")
    return list(args)

django.conf.urls.patterns = _compat_patterns

django.core.management.base.NoArgsCommand = django.core.management.base.BaseCommand
