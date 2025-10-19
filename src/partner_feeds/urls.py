# src/partner_feeds/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/partner/upload-feed/', views.upload_feed, name='upload_feed'),
]