from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from mailreporter.models import Report
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def mailReporter(request):

    reports = json.loads(request.body)

    # Possible Events:
    # processed, dropped, delivered, deferred, bounce, open, click, spam report, unsubscribe, group unsubscribe, and group resubscribe

    events_catch = ['bounce', 'dropped', 'spam report']

    categories_catch = []

    for report in reports:

        if report['event'] in events_catch:

            if 'category' not in report:

                new_report = Report(
                    report = report
                )
                new_report.save()

    return HttpResponse("Message received okay.", content_type="text/plain")

