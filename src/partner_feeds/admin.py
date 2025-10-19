from django.contrib import admin
from .models import Partner, FeedIngestion
from .services import FeedIngestionService
import os
from django.conf import settings
from django import forms

class PartnerAdminForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = '__all__'
    
    manual_upload = forms.FileField(required=False, help_text="Upload a feed file manually")

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ['name', 'feed_format', 'ingestion_schedule', 'is_active', 'created_at']
    list_filter = ['is_active', 'feed_format', 'ingestion_schedule']
    search_fields = ['name']
    readonly_fields = ['api_key']
    actions = ['process_manual_upload']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Handle manual file upload
        manual_file = form.cleaned_data.get('manual_upload')
        if manual_file:
            # Save uploaded file temporarily
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'partner_feeds')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"manual_upload_{obj.id}_{manual_file.name}")
            
            with open(file_path, 'wb+') as destination:
                for chunk in manual_file.chunks():
                    destination.write(chunk)
            
            # Process the file
            try:
                service = FeedIngestionService()
                ingestion = service.ingest_feed(obj.id, file_path)
                self.message_user(request, f"Manual upload processed: {ingestion.items_processed} items processed, {ingestion.items_failed} failed")
            except Exception as e:
                self.message_user(request, f"Manual upload failed: {str(e)}", level='error')

@admin.register(FeedIngestion)
class FeedIngestionAdmin(admin.ModelAdmin):
    list_display = ['partner', 'status', 'items_processed', 'items_failed', 'started_at']
    list_filter = ['status', 'partner']
    readonly_fields = ['started_at', 'completed_at']