# Monkey-patch removed Django APIs needed by old third-party packages
import django.conf.urls

if not hasattr(django.conf.urls, 'patterns'):
    def patterns(prefix, *args):
        """Compatibility shim for django.conf.urls.patterns (removed in Django 2.0)."""
        from django.urls import re_path
        pattern_list = []
        for t in args:
            if isinstance(t, (list, tuple)):
                t = re_path(*t)
            pattern_list.append(t)
        return pattern_list

    django.conf.urls.patterns = patterns
