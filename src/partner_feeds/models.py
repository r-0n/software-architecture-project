# src/partner_feeds/models.py
from django.db import models
import uuid

class Partner(models.Model):
    name = models.CharField(max_length=255)
    api_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    feed_format = models.CharField(max_length=10, choices=[('CSV', 'CSV'), ('JSON', 'JSON')])
    feed_url = models.URLField(blank=True, null=True)
    ingestion_schedule = models.CharField(max_length=20, choices=[
        ('MANUAL', 'Manual'),
        ('HOURLY', 'Hourly'),
        ('DAILY', 'Daily')
    ], default='MANUAL')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class FeedIngestion(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ], default='PENDING')
    file_path = models.CharField(max_length=500, blank=True)
    items_processed = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.partner.name} - {self.started_at}"