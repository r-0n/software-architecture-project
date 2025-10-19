# src/partner_feeds/validators.py
from django.core.exceptions import ValidationError
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ProductFeedValidator:
    REQUIRED_FIELDS = ['name', 'price', 'sku']
    
    def validate_item(self, item: Dict) -> List[str]:
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in item or not str(item[field]).strip():
                errors.append(f"Missing required field: {field}")
        
        # Validate price
        if 'price' in item:
            try:
                price = float(item['price'])
                if price <= 0:
                    errors.append("Price must be greater than 0")
            except (ValueError, TypeError):
                errors.append("Invalid price format")
        
        # Validate stock
        if 'stock_quantity' in item:
            try:
                stock = int(item['stock_quantity'])
                if stock < 0:
                    errors.append("Stock cannot be negative")
            except (ValueError, TypeError):
                errors.append("Invalid stock quantity format")
                
        return errors
    
    def transform_item(self, item: Dict, partner) -> Dict:
        """Transform partner-specific format to our product model"""
        transformed = {
            'name': str(item.get('name', '')).strip(),
            'description': str(item.get('description', '')),
            'price': float(item.get('price', 0)),
            'stock_quantity': int(item.get('stock_quantity', item.get('stock', 0))),
            'sku': str(item.get('sku', '')).strip(),
            'partner': partner,
            'is_active': True
        }
        
        # Handle category - you might want to create categories or use default
        # For now, we'll handle this in the service
        
        # Handle flash sale fields if present
        if 'flash_sale_price' in item and item['flash_sale_price']:
            transformed['flash_sale_price'] = float(item['flash_sale_price'])
            transformed['is_flash_sale'] = True
        if 'flash_sale_start' in item and item['flash_sale_start']:
            transformed['flash_sale_start'] = item['flash_sale_start']
        if 'flash_sale_end' in item and item['flash_sale_end']:
            transformed['flash_sale_end'] = item['flash_sale_end']
            
        return transformed