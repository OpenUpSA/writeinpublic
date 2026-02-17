from django.conf.urls import url
from mailit.views import IncomingMail
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    url('^inbound/sendgrid/raw/$',
        csrf_exempt(IncomingMail.as_view()), name='sendgrid_inbound_raw'),
]
