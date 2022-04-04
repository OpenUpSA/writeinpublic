from django.contrib import admin
from django.conf.urls import url
from mailreporter import views

urlpatterns = [
    url(r'mailreporter/', views.mailReporter, name='MailReporter'),
]