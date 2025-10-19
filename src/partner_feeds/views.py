# src/partner_feeds/views.py

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from .models import Partner
from .services import FeedIngestionService
import os
import uuid
from django.conf import settings

class PartnerAuthentication:
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        if api_key:
            try:
                return Partner.objects.get(api_key=api_key, is_active=True)
            except Partner.DoesNotExist:
                return None
        return None

@api_view(['POST'])
def upload_feed(request):
    """API endpoint for partners to upload their product feeds"""
    
    # Authenticate using API key
    authenticator = PartnerAuthentication()
    partner = authenticator.authenticate(request)
    if not partner:
        return Response(
            {'error': 'Invalid or missing API key'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check file in request
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Save file temporarily
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'partner_feeds')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{partner.id}_{uuid.uuid4()}_{file.name}")
    
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Process feed
    try:
        service = FeedIngestionService()
        ingestion = service.ingest_feed(partner.id, file_path)
        
        return Response({
            'ingestion_id': ingestion.id,
            'status': ingestion.status,
            'processed': ingestion.items_processed,
            'failed': ingestion.items_failed
        })
        
    except Exception as e:
        return Response(
            {'error': f'Processing failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )