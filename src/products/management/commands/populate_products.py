"""
Management command to populate sample products.
Usage: python manage.py populate_products
"""
from django.core.management.base import BaseCommand
from products.models import Product, Category


class Command(BaseCommand):
    help = 'Populates the database with sample products and categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing products and categories.'))

        # Create categories
        electronics, _ = Category.objects.get_or_create(
            name='Electronics',
            defaults={'description': 'Electronic devices and gadgets'}
        )
        
        clothing, _ = Category.objects.get_or_create(
            name='Clothing',
            defaults={'description': 'Apparel and fashion items'}
        )
        
        books, _ = Category.objects.get_or_create(
            name='Books',
            defaults={'description': 'Books and reading materials'}
        )
        
        home, _ = Category.objects.get_or_create(
            name='Home & Garden',
            defaults={'description': 'Home improvement and garden supplies'}
        )

        # Sample products
        products_data = [
            {
                'name': 'Wireless Bluetooth Headphones',
                'sku': 'ELEC-001',
                'description': 'High-quality wireless headphones with noise cancellation',
                'price': 99.99,
                'stock_quantity': 50,
                'category': electronics,
            },
            {
                'name': 'Smartphone 128GB',
                'sku': 'ELEC-002',
                'description': 'Latest generation smartphone with 128GB storage',
                'price': 599.99,
                'stock_quantity': 25,
                'category': electronics,
            },
            {
                'name': 'Laptop Stand',
                'sku': 'ELEC-003',
                'description': 'Ergonomic aluminum laptop stand',
                'price': 29.99,
                'stock_quantity': 100,
                'category': electronics,
            },
            {
                'name': 'Cotton T-Shirt',
                'sku': 'CLOTH-001',
                'description': 'Comfortable 100% cotton t-shirt',
                'price': 19.99,
                'stock_quantity': 200,
                'category': clothing,
            },
            {
                'name': 'Denim Jeans',
                'sku': 'CLOTH-002',
                'description': 'Classic fit denim jeans',
                'price': 49.99,
                'stock_quantity': 75,
                'category': clothing,
            },
            {
                'name': 'Running Shoes',
                'sku': 'CLOTH-003',
                'description': 'Lightweight running shoes with cushioned sole',
                'price': 79.99,
                'stock_quantity': 60,
                'category': clothing,
            },
            {
                'name': 'Python Programming Book',
                'sku': 'BOOK-001',
                'description': 'Comprehensive guide to Python programming',
                'price': 39.99,
                'stock_quantity': 30,
                'category': books,
            },
            {
                'name': 'Web Development Guide',
                'sku': 'BOOK-002',
                'description': 'Complete guide to modern web development',
                'price': 44.99,
                'stock_quantity': 25,
                'category': books,
            },
            {
                'name': 'Indoor Plant Pot Set',
                'sku': 'HOME-001',
                'description': 'Set of 3 ceramic plant pots',
                'price': 24.99,
                'stock_quantity': 80,
                'category': home,
            },
            {
                'name': 'Garden Tool Set',
                'sku': 'HOME-002',
                'description': 'Complete garden tool set with storage case',
                'price': 59.99,
                'stock_quantity': 40,
                'category': home,
            },
        ]

        created_count = 0
        updated_count = 0

        for product_data in products_data:
            product, created = Product.objects.update_or_create(
                sku=product_data['sku'],
                defaults={
                    'name': product_data['name'],
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'stock_quantity': product_data['stock_quantity'],
                    'category': product_data['category'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {product.name} (SKU: {product.sku})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {product.name} (SKU: {product.sku})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully populated products!\n'
                f'   Created: {created_count}\n'
                f'   Updated: {updated_count}\n'
                f'   Total products: {Product.objects.count()}\n'
                f'   Total categories: {Category.objects.count()}'
            )
        )

