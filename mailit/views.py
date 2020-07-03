import logging

from .forms import MailitTemplateForm
from .models import MailItTemplate
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail.message import EmailMultiAlternatives
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.edit import UpdateView
from instance.models import WriteItInstance
from mailit.answer import OutboundMessageAnswer
from mailit.bin.handleemail import EmailHandler
from mailit.exceptions import CouldNotFindIdentifier
from nuntium.models import OutboundMessageIdentifier
from subdomains.utils import reverse
import traceback

logger = logging.getLogger(__name__)


class MailitTemplateUpdateView(UpdateView):
    model = MailItTemplate
    form_class = MailitTemplateForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MailitTemplateUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self):
        self.writeitinstance = get_object_or_404(WriteItInstance, slug=self.request.subdomain)
        if not self.writeitinstance.owner.__eq__(self.request.user):
            raise Http404
        self.object = self.writeitinstance.mailit_template
        return self.object

    def get_form_kwargs(self):
        kwargs = super(MailitTemplateUpdateView, self).get_form_kwargs()
        self.object = self.get_object()
        kwargs['writeitinstance'] = self.object.writeitinstance
        return kwargs

    def get_success_url(self):
        return reverse('writeitinstance_template_update', subdomain=self.writeitinstance.slug)


def send_error_email(email):
    tb = traceback.format_exc()
    text_content = "Error the traceback was:\n" + tb
    #mail_admins('Error handling incoming email', html_message, html_message=html_message)
    subject = "Error handling incoming email"
    mail = EmailMultiAlternatives('%s%s' % (settings.EMAIL_SUBJECT_PREFIX, subject),
        text_content,  # content
        settings.DEFAULT_FROM_EMAIL,  # From
        [a[1] for a in settings.ADMINS],  # To
        )
    mail.attach('mail.txt', email, 'text/plain')
    mail.send()

class IncomingMail(View):
    """
    https://sendgrid.com/docs/API_Reference/Parse_Webhook/inbound_email.html
    """
    def get(self, request):
        logger.info("SendGrid Inbound mail webhook GET %r", request.GET)
        return HttpResponse()

    def post(self, request):
        handler = EmailHandler(answer_class=OutboundMessageAnswer)
        email = request.POST['email']

        try:
            logger.debug("SendGrid Inbound mail webhook POST email\n\n%s" % email)
            answer = handler.handle(email)
            answer.send_back()
        except CouldNotFindIdentifier as e:
            logger.warn(e)
        except OutboundMessageIdentifier.DoesNotExist:
            send_error_email(email)
        except Exception as e:
            send_error_email(email)
            raise e

        return HttpResponse()
