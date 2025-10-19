import os
import django
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retail.settings')
django.setup()

from partner_feeds.models import Partner
from partner_feeds.services import FeedIngestionService

def setup_test_partner():
    """Create a test partner for testing"""
    partner, created = Partner.objects.get_or_create(
        name='Test Partner Inc.',
        defaults={
            'feed_format': 'CSV',
            'is_active': True
        }
    )
    print(f"Partner: {partner.name}")
    print(f"API Key: {partner.api_key}")
    return partner

def test_csv_ingestion(partner):
    """Test CSV file ingestion"""
    print("\n=== Testing CSV Ingestion ===")
    service = FeedIngestionService()
    
    # Update partner to CSV format
    partner.feed_format = 'CSV'
    partner.save()
    
    # Use absolute path
    file_path = os.path.join(os.path.dirname(__file__), 'test_feeds', 'minimal_test.csv')
    print(f"Looking for file at: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        ingestion = service.ingest_feed(partner.id, file_path)
        print(f"CSV Ingestion Result:")
        print(f"Status: {ingestion.status}")
        print(f"Processed: {ingestion.items_processed}")
        print(f"Failed: {ingestion.items_failed}")
    except Exception as e:
        print(f"CSV Ingestion Failed: {e}")

def test_direct_upload():
    """Test the upload functionality directly"""
    print("\n=== Testing Direct Upload ===")
    
    # Check if we can access the partner API
    from django.test import Client
    from partner_feeds.models import Partner
    import json
    
    client = Client()
    partner = Partner.objects.first()
    
    if not partner:
        print("No partners found. Please create a partner first in admin.")
        return
    
    print(f"Testing with partner: {partner.name}")
    print(f"API Key: {partner.api_key}")
    
    # Test with minimal CSV
    csv_content = """name,sku,price,stock_quantity,category
Test Direct Product,DIRECT-001,15.99,25,Electronics
Test Direct Product 2,DIRECT-002,25.99,15,Home"""
    
    # This would simulate an API call - you can test this after setting up the views
    print("API endpoint ready at: /partner/api/partner/upload-feed/")

if __name__ == '__main__':
    print("Setting up test partner...")
    partner = setup_test_partner()
    
    test_csv_ingestion(partner)
    test_direct_upload()
    
    print("\n=== Testing Complete ===")
    print("\nNext steps:")
    print("1. Visit /admin to see partners and ingestion history")
    print("2. Visit /partner/upload-demo/ to test file uploads")
    print("3. Use the API keys to test via Postman or curl")