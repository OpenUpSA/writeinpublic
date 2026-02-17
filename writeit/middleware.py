import re
import threading

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

lower = lambda s: s.lower() if s else s


class SubdomainURLRoutingMiddleware(MiddlewareMixin):
    """Django 3 compatible replacement for subdomains.middleware.SubdomainURLRoutingMiddleware."""

    def get_domain_for_request(self, request):
        return lower(settings.SESSION_COOKIE_DOMAIN) or lower(request.get_host())

    def process_request(self, request):
        domain = self.get_domain_for_request(request)
        host = lower(request.get_host())
        pattern = r'^(?:(?P<subdomain>.*?)\.)?%s(?::.*)?$' % re.escape(domain)
        matches = re.match(pattern, host)
        if matches:
            request.subdomain = matches.group('subdomain')
        else:
            request.subdomain = None

        urlconf = None
        if hasattr(settings, 'SUBDOMAIN_URLCONFS'):
            urlconf = settings.SUBDOMAIN_URLCONFS.get(request.subdomain)
        if urlconf is not None:
            request.urlconf = urlconf

    def process_response(self, request, response):
        if getattr(settings, 'FORCE_VARY_ON_HOST', True):
            patch_vary_headers(response, ('Host',))
        return response


class PaginationMiddleware(MiddlewareMixin):
    """Django 3 compatible replacement for pagination.middleware.PaginationMiddleware."""

    def process_request(self, request):
        def get_page(suffix=''):
            try:
                return int(request.GET.get('page%s' % suffix, 1))
            except (ValueError, TypeError):
                return 1
        request.page = get_page


class SubdomainInThreadLocalStorageMiddleware(MiddlewareMixin):

    tls = threading.local()

    def process_request(self, request):
        # Set the subdomain in thread-local storage, so that we can
        # use it in a custom template loader.
        if hasattr(request, 'subdomain'):
            self.tls.subdomain = request.subdomain
        else:
            self.tls.subdomain = None

    def process_response(self, request, response):
        # Remove the subdomain attribute from thread-local storage on
        # the way back up the middleware processing, just before
        # returning the response to the browser. This looks like it
        # shouldn't make any difference (since the subdomain attribute
        # is created again on each process_request) but in fact it
        # does for tests: if the subdomain attribute still exists in
        # the thread-local storage, tests that use templates outside
        # of HTTP requests might pass when they should fail.
        try:
            delattr(self.tls, 'subdomain')
        except AttributeError:
            pass
        return response
