from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'Create sample categories for testing'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and accessories'
            },
            {
                'name': 'Clothing',
                'description': 'Apparel and fashion items'
            },
            {
                'name': 'Books',
                'description': 'Books, magazines, and educational materials'
            },
            {
                'name': 'Home & Garden',
                'description': 'Home improvement and garden supplies'
            },
            {
                'name': 'Sports & Outdoors',
                'description': 'Sports equipment and outdoor gear'
            },
            {
                'name': 'Health & Beauty',
                'description': 'Health and beauty products'
            },
            {
                'name': 'Toys & Games',
                'description': 'Toys, games, and entertainment items'
            },
            {
                'name': 'Food & Beverages',
                'description': 'Food items and beverages'
            }
        ]

        created_count = 0
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        )
