# src/partner_feeds/admin.py
from django.contrib import admin
from .models import Partner, FeedIngestion

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'feed_format', 'ingestion_schedule', 'is_active', 'created_at']
    list_filter = ['is_active', 'feed_format', 'ingestion_schedule']
    search_fields = ['name']
    readonly_fields = ['api_key']

@admin.register(FeedIngestion)
class FeedIngestionAdmin(admin.ModelAdmin):
    list_display = ['partner', 'status', 'items_processed', 'items_failed', 'started_at']
    list_filter = ['status', 'partner']
    readonly_fields = ['started_at', 'completed_at']