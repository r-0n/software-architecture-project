import os
import django
import sys
import glob
import json
import csv
from pathlib import Path

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retail.settings')
django.setup()

from partner_feeds.models import Partner, FeedIngestion
from partner_feeds.services import FeedIngestionService
from products.models import Product, Category

class PartnerFeedTester:
    def __init__(self):
        self.service = FeedIngestionService()
        self.test_feeds_dir = os.path.join(os.path.dirname(__file__), 'test_feeds')
        self.results = []
    
    def setup_test_partner(self, name="Test Partner Inc."):
        """Create or get a test partner"""
        partner, created = Partner.objects.get_or_create(
            name=name,
            defaults={
                'feed_format': 'CSV',
                'is_active': True
            }
        )
        return partner
    
    def discover_test_files(self):
        """Find all CSV and JSON files in test_feeds directory"""
        csv_files = glob.glob(os.path.join(self.test_feeds_dir, "*.csv"))
        json_files = glob.glob(os.path.join(self.test_feeds_dir, "*.json"))
        return csv_files + json_files
    
    def detect_file_format(self, file_path):
        """Detect if file is CSV or JSON based on extension and content"""
        ext = Path(file_path).suffix.lower()
        if ext == '.csv':
            return 'CSV'
        elif ext == '.json':
            return 'JSON'
        else:
            # Try to detect by content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('[') or first_line.startswith('{'):
                        return 'JSON'
                    else:
                        return 'CSV'
            except:
                return 'CSV'  # Default to CSV
    
    def validate_file_structure(self, file_path, format_type):
        """Basic validation of file structure"""
        try:
            if format_type == 'CSV':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    required_fields = ['name', 'sku', 'price']
                    missing_fields = [field for field in required_fields if field not in headers]
                    if missing_fields:
                        return False, f"Missing required fields: {missing_fields}"
                    return True, f"Valid CSV with {len(headers)} columns"
            
            elif format_type == 'JSON':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        return False, "JSON root should be an array"
                    if len(data) == 0:
                        return False, "JSON array is empty"
                    first_item = data[0]
                    required_fields = ['name', 'sku', 'price']
                    missing_fields = [field for field in required_fields if field not in first_item]
                    if missing_fields:
                        return False, f"Missing required fields in first item: {missing_fields}"
                    return True, f"Valid JSON with {len(data)} items"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def analyze_file_content(self, file_path, format_type):
        """Analyze file content for reporting"""
        try:
            if format_type == 'CSV':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    return {
                        'total_items': len(rows),
                        'columns': reader.fieldnames,
                        'sample_item': rows[0] if rows else {}
                    }
            
            elif format_type == 'JSON':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'total_items': len(data),
                        'columns': list(data[0].keys()) if data else [],
                        'sample_item': data[0] if data else {}
                    }
        
        except Exception as e:
            return {'error': str(e)}
    
    def run_single_test(self, file_path, partner_name=None):
        """Run ingestion test for a single file"""
        filename = os.path.basename(file_path)
        format_type = self.detect_file_format(file_path)
        
        print(f"\n{'='*60}")
        print(f"Testing: {filename}")
        print(f"Format: {format_type}")
        print(f"{'='*60}")
        
        # Validate file structure
        is_valid, validation_msg = self.validate_file_structure(file_path, format_type)
        if not is_valid:
            print(f"❌ Invalid file: {validation_msg}")
            self.results.append({
                'file': filename,
                'status': 'FAILED',
                'reason': f'Validation failed: {validation_msg}',
                'items_processed': 0,
                'items_failed': 0
            })
            return
        
        # Analyze content
        analysis = self.analyze_file_content(file_path, format_type)
        print(f"📊 File analysis: {analysis.get('total_items', 0)} items")
        if 'columns' in analysis:
            print(f"   Columns: {', '.join(analysis['columns'])}")
        
        # Setup partner
        partner = self.setup_test_partner(partner_name or f"Partner_{Path(filename).stem}")
        partner.feed_format = format_type
        partner.save()
        
        print(f"🤝 Using partner: {partner.name} (API Key: {partner.api_key})")
        
        # Run ingestion
        try:
            ingestion = self.service.ingest_feed(partner.id, file_path)
            
            print(f"✅ Ingestion completed!")
            print(f"   Status: {ingestion.status}")
            print(f"   Processed: {ingestion.items_processed} items")
            print(f"   Failed: {ingestion.items_failed} items")
            
            if ingestion.items_failed > 0:
                print(f"   Error: {ingestion.error_message}")
            
            # Verify results in database
            imported_products = Product.objects.filter(partner=partner)
            print(f"   📦 Products in DB: {imported_products.count()}")
            
            self.results.append({
                'file': filename,
                'status': 'SUCCESS',
                'partner': partner.name,
                'items_processed': ingestion.items_processed,
                'items_failed': ingestion.items_failed,
                'db_products_count': imported_products.count(),
                'error_message': ingestion.error_message
            })
            
        except Exception as e:
            print(f"❌ Ingestion failed: {str(e)}")
            self.results.append({
                'file': filename,
                'status': 'FAILED',
                'reason': str(e),
                'items_processed': 0,
                'items_failed': 0
            })
    
    def run_all_tests(self):
        """Run tests on all discovered files"""
        print("🔍 Discovering test files...")
        test_files = self.discover_test_files()
        
        if not test_files:
            print("❌ No test files found in test_feeds directory!")
            return
        
        print(f"📁 Found {len(test_files)} test files:")
        for file_path in test_files:
            print(f"   - {os.path.basename(file_path)}")
        
        # Clear previous test data
        self.cleanup_test_data()
        
        # Run tests
        for file_path in test_files:
            self.run_single_test(file_path)
        
        # Print summary
        self.print_summary()
    
    def cleanup_test_data(self):
        """Clean up previous test data"""
        print("\n🧹 Cleaning up previous test data...")
        
        # Delete test partners and their products
        test_partners = Partner.objects.filter(name__startswith="Partner_")
        partner_count = test_partners.count()
        
        for partner in test_partners:
            Product.objects.filter(partner=partner).delete()
        
        test_partners.delete()
        
        # Delete all ingestion records
        FeedIngestion.objects.all().delete()
        
        print(f"   Deleted {partner_count} test partners and their data")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        
        successful = [r for r in self.results if r['status'] == 'SUCCESS']
        failed = [r for r in self.results if r['status'] == 'FAILED']
        
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"📁 Total files: {len(self.results)}")
        
        if successful:
            print(f"\n📈 Successful tests:")
            for result in successful:
                print(f"   ✓ {result['file']}")
                print(f"     Processed: {result['items_processed']}, Failed: {result['items_failed']}")
                print(f"     DB Products: {result['db_products_count']}")
        
        if failed:
            print(f"\n📉 Failed tests:")
            for result in failed:
                print(f"   ✗ {result['file']}")
                print(f"     Reason: {result['reason']}")
        
        # Database overview
        total_products = Product.objects.count()
        partner_products = Product.objects.filter(partner__isnull=False).count()
        categories = Category.objects.count()
        
        print(f"\n🏪 Database Overview:")
        print(f"   Total Products: {total_products}")
        print(f"   Partner Products: {partner_products}")
        print(f"   Categories: {categories}")
        
        # Show sample of imported products
        if partner_products > 0:
            print(f"\n📦 Sample Imported Products:")
            sample_products = Product.objects.filter(partner__isnull=False)[:3]
            for product in sample_products:
                print(f"   - {product.name} (SKU: {product.sku}) - ${product.price}")

def main():
    """Main test runner"""
    print("🚀 Starting Partner Feed Ingestion Test Suite")
    print("This will test all CSV and JSON files in the test_feeds directory")
    
    tester = PartnerFeedTester()
    tester.run_all_tests()

if __name__ == '__main__':
    main()