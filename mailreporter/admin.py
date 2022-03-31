from django.contrib import admin
from django import forms

import logging

logger = logging.getLogger(__name__)

from mailreporter.models import Report

@admin.register(Report)
class MailReporterAdmin(admin.ModelAdmin):
      search_fields = ['report']
      list_display = ['email', 'event', 'type', 'reason', 'timestamp', 'processed', 'contact']
      list_display_links = ['reason']
      list_filter = ['processed']
      fieldsets = [
        (None, {
            'fields': ['report','processed'],
            'classes': ['wide']
        }
      )]
      change_form_template = 'admin/mailreporter/change_form.html'

      def has_add_permission(self, request):
        return False