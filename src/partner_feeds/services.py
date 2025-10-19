# src/partner_feeds/services.py
import os
from django.conf import settings
from .models import Partner, FeedIngestion
from .adapters import FeedAdapterFactory
from .validators import ProductFeedValidator
from products.models import Product, Category
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class FeedIngestionService:
    def __init__(self):
        self.validator = ProductFeedValidator()
    
    def ingest_feed(self, partner_id: int, file_path: str) -> FeedIngestion:
        """Main ingestion method"""
        try:
            partner = Partner.objects.get(id=partner_id)
            ingestion = FeedIngestion.objects.create(
                partner=partner,
                status='PROCESSING',
                file_path=file_path
            )
            
            # Get appropriate adapter
            adapter = FeedAdapterFactory.get_adapter(partner.feed_format)
            if not adapter:
                raise ValueError(f"Unsupported format: {partner.feed_format}")
            
            # Parse feed
            items = adapter.parse(file_path)
            
            # Process each item
            processed = 0
            failed = 0
            
            for item in items:
                try:
                    self._process_single_item(item, partner)
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process item: {e}")
                    failed += 1
            
            # Update ingestion record
            ingestion.status = 'COMPLETED'
            ingestion.items_processed = processed
            ingestion.items_failed = failed
            ingestion.save()
            
            logger.info(f"Successfully processed {processed} items, {failed} failed")
            return ingestion
            
        except Exception as e:
            logger.error(f"Feed ingestion failed: {e}")
            if 'ingestion' in locals():
                ingestion.status = 'FAILED'
                ingestion.error_message = str(e)
                ingestion.save()
            raise
    
    def _process_single_item(self, item: Dict, partner: Partner):
        """Process a single product item"""
        # Validate
        errors = self.validator.validate_item(item)
        if errors:
            raise ValidationError(f"Validation errors: {', '.join(errors)}")
        
        # Transform
        product_data = self.validator.transform_item(item, partner)
        
        # Handle category - create a default category if none provided
        category_name = item.get('category', 'General')
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'description': f'Auto-created category for {category_name}'}
        )
        product_data['category'] = category
        
        # Remove partner from data since we're passing it separately
        partner_ref = product_data.pop('partner')
        
        # Upsert (update or create)
        Product.objects.update_or_create(
            sku=product_data['sku'],
            partner=partner_ref,
            defaults=product_data
        )