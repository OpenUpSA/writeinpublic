from mailit.bin.handleemail import EmailAnswer
from mailit.models import BouncedMessageRecord
from nuntium.models import OutboundMessageIdentifier, OutboundMessage, OutboundMessagePluginRecord, AnswerAttachment
from django.core.files import File
from django.conf import settings


class OutboundMessageAnswer(EmailAnswer):
    def save(self):
        answer = OutboundMessageIdentifier.create_answer(self.outbound_message_identifier, self.content_text)
        return answer

    def save_attachment(self, answer, attachment):
        the_file = File(attachment)
        answer_attachment = AnswerAttachment(answer=answer,
                                content=the_file,
                                name=attachment.name)
        answer_attachment.save()

    def report_bounce(self):

        if settings.FLAG_BOUNCED_CONTACTS:

            identifier = OutboundMessageIdentifier.objects.get(key=self.outbound_message_identifier)
            outbound_message = OutboundMessage.objects.get(outboundmessageidentifier=identifier)
            outbound_message.status = 'error'
            outbound_message.save()
            records = OutboundMessagePluginRecord.objects.filter(outbound_message=outbound_message)
            for record in records:
                record.try_again = True
                record.save()
            BouncedMessageRecord.objects.create(outbound_message=outbound_message, bounce_text=self.content_text)
            contact = outbound_message.contact
            contact.is_bounced = True
            contact.save()
