from django.db import models
from django.utils.html import format_html
from datetime import datetime
import jsonfield
 
class Report(models.Model):
    report = jsonfield.JSONField()
    resolved = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True, null=True)

    def email(self):
        return format_html('<strong>{}</strong>', self.report["email"])

    def contact(self):
        return format_html('<a href="/admin/contactos/contact/?q={}">Open Contact</>', self.report["email"])

    def event(self):
        return self.report["event"]
    
    def type(self):
        return self.report["type"] if "type" in self.report else ''

    def reason(self):
        return self.report["reason"][0:60] if "reason" in self.report else ''
    
    def timestamp(self):
        return datetime.fromtimestamp(self.report["timestamp"])