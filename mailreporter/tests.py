# coding=utf-8
from django.test import TestCase
from django.test import Client
import json
from mailreporter.models import Report

class MailReporter(TestCase):

    def test_a_report_is_captured_with_the_webhook(self):
        report = [
            {
                "email": "example@test.com",
                "event": "bounce",
                "reason": "500 unknown recipient",
                "status": "5.0.0",
                "category": ["writeinpublic"],
                "smtp-id": "<14c5d75ce93.dfd.64b469@ismtpd-555>",
                "timestamp": 1648619617,
                "sg_event_id": "V2P95uf6VQV49Jdwzg5iwQ==",
                "sg_message_id": "14c5d75ce93.dfd.64b469.filter0001.16648.5515E0B88.0"
            }
        ]

        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        self.assertEquals(Report.objects.count(), 1)

    def test_only_bounce_dropped_captured(self):
        report = [
            {
                "email": "example@test.com",
                "event": "dropped",
                "reason": "Bounced Address",
                "status": "5.0.0",
                "category": ["writeinpublic"],
                "smtp-id": "<14c5d75ce93.dfd.64b469@ismtpd-555>",
                "timestamp": 1648619617,
                "sg_event_id": "oCajGXZz9KUdMvCqf3Kshw==",
                "sg_message_id": "14c5d75ce93.dfd.64b469.filter0001.16648.5515E0B88.0"
            }
        ]

        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        report[0]["event"] = "bounce"
        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        report[0]["event"] = "open"
        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        self.assertEquals(Report.objects.count(), 2)


    def test_only_report_with_correct_category_is_captured(self):
        # wrong category
        report = [
            {
                "email": "example@test.com",
                "event": "bounce",
                "reason": "500 unknown recipient",
                "status": "5.0.0",
                "smtp-id": "<14c5d75ce93.dfd.64b469@ismtpd-555>",
                "category": ["cat facts"],
                "timestamp": 1648619617,
                "sg_event_id": "V2P95uf6VQV49Jdwzg5iwQ==",
                "sg_message_id": "14c5d75ce93.dfd.64b469.filter0001.16648.5515E0B88.0"
            }
        ]
        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        self.assertEquals(Report.objects.count(), 0)

        # no category
        del report[0]["category"]
        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        self.assertEquals(Report.objects.count(), 0)

        # correct category
        report[0]["category"] = ["writeinpublic"]
        response = Client().post('/mailreporter/', json.dumps(report), content_type="application/json")
        self.assertEquals(Report.objects.count(), 1)
