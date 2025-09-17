from django.core.management.base import BaseCommand
from products.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create categories and products
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and accessories',
                'products': [
                    {'name': 'iPhone 15 Pro', 'sku': 'ELC-IPH15P-001', 'price': Decimal('999.99'), 'description': 'Latest iPhone with titanium design and advanced camera system', 'stock': 25},
                    {'name': 'Samsung Galaxy S24', 'sku': 'ELC-SAM24-002', 'price': Decimal('899.99'), 'description': 'Premium Android smartphone with AI-powered features', 'stock': 30},
                    {'name': 'MacBook Air M3', 'sku': 'ELC-MBA-M3-003', 'price': Decimal('1299.99'), 'description': 'Ultra-thin laptop with M3 chip and all-day battery life', 'stock': 15},
                    {'name': 'Sony WH-1000XM5', 'sku': 'ELC-SON-WH-004', 'price': Decimal('399.99'), 'description': 'Industry-leading noise canceling wireless headphones', 'stock': 40},
                    {'name': 'iPad Pro 12.9"', 'sku': 'ELC-IPD-PRO-005', 'price': Decimal('1099.99'), 'description': 'Professional tablet with M2 chip and Liquid Retina display', 'stock': 20},
                    {'name': 'Nintendo Switch OLED', 'sku': 'ELC-NIN-SW-006', 'price': Decimal('349.99'), 'description': 'Gaming console with vibrant OLED screen and enhanced audio', 'stock': 35},
                    {'name': 'Dell XPS 13', 'sku': 'ELC-DEL-XPS-007', 'price': Decimal('1199.99'), 'description': 'Premium ultrabook with InfinityEdge display', 'stock': 18},
                    {'name': 'AirPods Pro 2nd Gen', 'sku': 'ELC-AP-PRO-008', 'price': Decimal('249.99'), 'description': 'Wireless earbuds with active noise cancellation', 'stock': 50},
                    {'name': 'Canon EOS R6 Mark II', 'sku': 'ELC-CAN-R6-009', 'price': Decimal('2499.99'), 'description': 'Professional mirrorless camera with 4K video recording', 'stock': 12},
                    {'name': 'LG OLED C3 55"', 'sku': 'ELC-LG-C3-010', 'price': Decimal('1399.99'), 'description': 'Premium OLED TV with AI-powered picture optimization', 'stock': 8}
                ]
            },
            {
                'name': 'Clothing',
                'description': 'Apparel and fashion items',
                'products': [
                    {'name': 'Nike Air Max 270', 'sku': 'CLT-NIK-AM-001', 'price': Decimal('150.99'), 'description': 'Comfortable running shoes with Max Air cushioning', 'stock': 60},
                    {'name': 'Levi\'s 501 Original Jeans', 'sku': 'CLT-LEV-501-002', 'price': Decimal('89.99'), 'description': 'Classic straight-fit jeans in authentic blue denim', 'stock': 45},
                    {'name': 'Adidas Ultraboost 22', 'sku': 'CLT-ADI-UB-003', 'price': Decimal('180.99'), 'description': 'High-performance running shoes with Boost midsole', 'stock': 35},
                    {'name': 'Patagonia Better Sweater', 'sku': 'CLT-PAT-BS-004', 'price': Decimal('119.99'), 'description': 'Sustainable fleece jacket made from recycled materials', 'stock': 25},
                    {'name': 'Uniqlo Heattech Long Sleeve', 'sku': 'CLT-UNI-HT-005', 'price': Decimal('19.99'), 'description': 'Thermal base layer with advanced heat retention technology', 'stock': 80},
                    {'name': 'Zara Oversized Blazer', 'sku': 'CLT-ZAR-OB-006', 'price': Decimal('79.99'), 'description': 'Modern blazer with relaxed fit and contemporary styling', 'stock': 30},
                    {'name': 'H&M Cotton T-Shirt', 'sku': 'CLT-HM-CT-007', 'price': Decimal('12.99'), 'description': 'Basic cotton t-shirt in various colors and sizes', 'stock': 100},
                    {'name': 'North Face Summit Series Jacket', 'sku': 'CLT-NTF-SS-008', 'price': Decimal('199.99'), 'description': 'Weather-resistant jacket for outdoor adventures', 'stock': 20},
                    {'name': 'Champion Reverse Weave Hoodie', 'sku': 'CLT-CHM-RW-009', 'price': Decimal('65.99'), 'description': 'Classic hoodie with anti-shrink cotton construction', 'stock': 40},
                    {'name': 'Vans Old Skool Sneakers', 'sku': 'CLT-VAN-OS-010', 'price': Decimal('65.99'), 'description': 'Iconic skateboarding shoes with signature side stripe', 'stock': 55}
                ]
            },
            {
                'name': 'Books',
                'description': 'Books, magazines, and educational materials',
                'products': [
                    {'name': 'The Great Gatsby', 'sku': 'BOK-GAT-GG-001', 'price': Decimal('12.99'), 'description': 'Classic American novel by F. Scott Fitzgerald', 'stock': 75},
                    {'name': 'To Kill a Mockingbird', 'sku': 'BOK-LEE-TK-002', 'price': Decimal('14.99'), 'description': 'Harper Lee\'s masterpiece about justice and morality', 'stock': 60},
                    {'name': '1984 by George Orwell', 'sku': 'BOK-ORW-84-003', 'price': Decimal('13.99'), 'description': 'Dystopian novel about totalitarian control', 'stock': 50},
                    {'name': 'Pride and Prejudice', 'sku': 'BOK-AUS-PP-004', 'price': Decimal('11.99'), 'description': 'Jane Austen\'s romantic novel about Elizabeth Bennet', 'stock': 45},
                    {'name': 'The Catcher in the Rye', 'sku': 'BOK-SAL-CR-005', 'price': Decimal('13.99'), 'description': 'J.D. Salinger\'s coming-of-age story', 'stock': 40},
                    {'name': 'Lord of the Flies', 'sku': 'BOK-GOL-LF-006', 'price': Decimal('12.99'), 'description': 'William Golding\'s allegorical novel about human nature', 'stock': 35},
                    {'name': 'The Hobbit', 'sku': 'BOK-TOL-HB-007', 'price': Decimal('15.99'), 'description': 'J.R.R. Tolkien\'s fantasy adventure novel', 'stock': 55},
                    {'name': 'Harry Potter and the Sorcerer\'s Stone', 'sku': 'BOK-ROW-HP-008', 'price': Decimal('16.99'), 'description': 'First book in the magical Harry Potter series', 'stock': 80},
                    {'name': 'The Chronicles of Narnia', 'sku': 'BOK-LEW-CN-009', 'price': Decimal('14.99'), 'description': 'C.S. Lewis\'s fantasy series about magical adventures', 'stock': 30},
                    {'name': 'The Alchemist', 'sku': 'BOK-COE-AL-010', 'price': Decimal('13.99'), 'description': 'Paulo Coelho\'s inspirational novel about following dreams', 'stock': 65}
                ]
            },
            {
                'name': 'Home & Garden',
                'description': 'Home improvement and garden supplies',
                'products': [
                    {'name': 'Dyson V15 Detect Vacuum', 'sku': 'HOM-DYS-V15-001', 'price': Decimal('649.99'), 'description': 'Cordless vacuum with laser dust detection technology', 'stock': 15},
                    {'name': 'KitchenAid Stand Mixer', 'sku': 'HOM-KIT-SM-002', 'price': Decimal('399.99'), 'description': 'Professional-grade stand mixer in classic colors', 'stock': 20},
                    {'name': 'Instant Pot Duo 7-in-1', 'sku': 'HOM-INS-DUO-003', 'price': Decimal('99.99'), 'description': 'Multi-functional pressure cooker and slow cooker', 'stock': 35},
                    {'name': 'Philips Hue Smart Bulbs', 'sku': 'HOM-PHI-HUE-004', 'price': Decimal('49.99'), 'description': 'WiFi-enabled LED bulbs with millions of colors', 'stock': 50},
                    {'name': 'Weber Genesis II Gas Grill', 'sku': 'HOM-WEB-GEN-005', 'price': Decimal('699.99'), 'description': 'Premium gas grill with GS4 grilling system', 'stock': 12},
                    {'name': 'Roomba i7+ Robot Vacuum', 'sku': 'HOM-ROO-I7-006', 'price': Decimal('799.99'), 'description': 'Self-emptying robot vacuum with smart mapping', 'stock': 18},
                    {'name': 'Nest Learning Thermostat', 'sku': 'HOM-NES-LT-007', 'price': Decimal('249.99'), 'description': 'Smart thermostat that learns your schedule', 'stock': 25},
                    {'name': 'Vitamix A3500 Blender', 'sku': 'HOM-VIT-A35-008', 'price': Decimal('549.99'), 'description': 'Professional blender with preset programs', 'stock': 22},
                    {'name': 'Ring Video Doorbell Pro', 'sku': 'HOM-RIN-VDP-009', 'price': Decimal('199.99'), 'description': 'HD video doorbell with advanced motion detection', 'stock': 30},
                    {'name': 'Breville Barista Express', 'sku': 'HOM-BRE-BE-010', 'price': Decimal('599.99'), 'description': 'Espresso machine with built-in grinder', 'stock': 16}
                ]
            },
            {
                'name': 'Sports & Outdoors',
                'description': 'Sports equipment and outdoor gear',
                'products': [
                    {'name': 'Wilson Pro Staff Tennis Racket', 'sku': 'SPT-WIL-PS-001', 'price': Decimal('249.99'), 'description': 'Professional tennis racket used by top players', 'stock': 25},
                    {'name': 'Callaway Mavrik Driver', 'sku': 'SPT-CAL-MAV-002', 'price': Decimal('399.99'), 'description': 'Golf driver with AI-designed face for maximum distance', 'stock': 18},
                    {'name': 'Yeti Rambler Tumbler', 'sku': 'SPT-YET-RAM-003', 'price': Decimal('35.99'), 'description': 'Insulated tumbler that keeps drinks hot or cold', 'stock': 60},
                    {'name': 'Patagonia Black Hole Duffel', 'sku': 'SPT-PAT-BH-004', 'price': Decimal('129.99'), 'description': 'Durable travel duffel made from recycled materials', 'stock': 40},
                    {'name': 'Coleman Sundome Tent', 'sku': 'SPT-COL-SUN-005', 'price': Decimal('89.99'), 'description': 'Easy-to-set-up camping tent for 4 people', 'stock': 30},
                    {'name': 'Hydro Flask Water Bottle', 'sku': 'SPT-HYD-FL-006', 'price': Decimal('29.99'), 'description': 'Insulated stainless steel water bottle', 'stock': 80},
                    {'name': 'Arc\'teryx Beta AR Jacket', 'sku': 'SPT-ARC-BAR-007', 'price': Decimal('399.99'), 'description': 'Lightweight waterproof shell for outdoor activities', 'stock': 15},
                    {'name': 'Black Diamond Headlamp', 'sku': 'SPT-BLD-HL-008', 'price': Decimal('49.99'), 'description': 'Bright LED headlamp for hiking and camping', 'stock': 45},
                    {'name': 'Osprey Atmos AG Backpack', 'sku': 'SPT-OSP-ATM-009', 'price': Decimal('199.99'), 'description': 'Comfortable hiking backpack with anti-gravity suspension', 'stock': 22},
                    {'name': 'Salomon Speedcross Trail Shoes', 'sku': 'SPT-SAL-SC-010', 'price': Decimal('129.99'), 'description': 'Trail running shoes with aggressive grip', 'stock': 35}
                ]
            },
            {
                'name': 'Health & Beauty',
                'description': 'Health and beauty products',
                'products': [
                    {'name': 'Oral-B Genius X Toothbrush', 'sku': 'HLT-ORB-GX-001', 'price': Decimal('199.99'), 'description': 'Smart electric toothbrush with AI coaching', 'stock': 40},
                    {'name': 'Foreo Luna 3 Facial Cleanser', 'sku': 'HLT-FOR-LU-002', 'price': Decimal('199.99'), 'description': 'Sonic facial cleansing device with T-Sonic technology', 'stock': 25},
                    {'name': 'Philips Sonicare DiamondClean', 'sku': 'HLT-PHI-SD-003', 'price': Decimal('219.99'), 'description': 'Premium electric toothbrush with diamond clean heads', 'stock': 30},
                    {'name': 'Dyson Supersonic Hair Dryer', 'sku': 'HLT-DYS-SS-004', 'price': Decimal('399.99'), 'description': 'High-speed hair dryer with intelligent heat control', 'stock': 18},
                    {'name': 'Clarisonic Mia Smart Facial Brush', 'sku': 'HLT-CLA-MIA-005', 'price': Decimal('149.99'), 'description': 'Sonic facial cleansing brush with smart connectivity', 'stock': 22},
                    {'name': 'Fitbit Versa 3 Smartwatch', 'sku': 'HLT-FIT-V3-006', 'price': Decimal('199.99'), 'description': 'Health and fitness smartwatch with GPS', 'stock': 35},
                    {'name': 'TheraGun Elite Massage Device', 'sku': 'HLT-THE-EL-007', 'price': Decimal('399.99'), 'description': 'Professional-grade percussion therapy device', 'stock': 20},
                    {'name': 'NuFACE Trinity Facial Toning Device', 'sku': 'HLT-NUF-TR-008', 'price': Decimal('339.99'), 'description': 'Microcurrent facial toning device for anti-aging', 'stock': 15},
                    {'name': 'Garmin Venu 2 Fitness Watch', 'sku': 'HLT-GAR-V2-009', 'price': Decimal('299.99'), 'description': 'GPS fitness watch with health monitoring features', 'stock': 28},
                    {'name': 'Braun Series 9 Electric Shaver', 'sku': 'HLT-BRA-S9-010', 'price': Decimal('299.99'), 'description': 'Premium electric shaver with intelligent shaving system', 'stock': 25}
                ]
            },
            {
                'name': 'Toys & Games',
                'description': 'Toys, games, and entertainment items',
                'products': [
                    {'name': 'LEGO Creator Expert Modular Building', 'sku': 'TOY-LEG-CE-001', 'price': Decimal('179.99'), 'description': 'Detailed modular building set for adult collectors', 'stock': 20},
                    {'name': 'PlayStation 5 Console', 'sku': 'TOY-PS5-CON-002', 'price': Decimal('499.99'), 'description': 'Next-generation gaming console with ultra-fast SSD', 'stock': 8},
                    {'name': 'Xbox Series X Console', 'sku': 'TOY-XBX-SX-003', 'price': Decimal('499.99'), 'description': 'Powerful gaming console with 4K gaming capabilities', 'stock': 10},
                    {'name': 'Magic: The Gathering Commander Deck', 'sku': 'TOY-MTG-CD-004', 'price': Decimal('39.99'), 'description': 'Pre-constructed commander deck for multiplayer games', 'stock': 50},
                    {'name': 'Rubik\'s Cube Speed Cube', 'sku': 'TOY-RUB-SC-005', 'price': Decimal('19.99'), 'description': 'Professional speed cube for competitive solving', 'stock': 75},
                    {'name': 'Monopoly Ultimate Banking Edition', 'sku': 'TOY-MON-UB-006', 'price': Decimal('29.99'), 'description': 'Modern version of the classic board game', 'stock': 40},
                    {'name': 'Pokemon Trading Card Game Booster Box', 'sku': 'TOY-POK-TCG-007', 'price': Decimal('119.99'), 'description': '36 booster packs of Pokemon trading cards', 'stock': 25},
                    {'name': 'Jenga Giant Hardwood Game', 'sku': 'TOY-JEN-GH-008', 'price': Decimal('49.99'), 'description': 'Oversized Jenga game with hardwood blocks', 'stock': 30},
                    {'name': 'Settlers of Catan Board Game', 'sku': 'TOY-SET-CAT-009', 'price': Decimal('44.99'), 'description': 'Strategy board game about building settlements', 'stock': 35},
                    {'name': 'Nerf Rival Prometheus Blaster', 'sku': 'TOY-NER-PRO-010', 'price': Decimal('99.99'), 'description': 'High-capacity foam dart blaster for competitive play', 'stock': 15}
                ]
            },
            {
                'name': 'Food & Beverages',
                'description': 'Food items and beverages',
                'products': [
                    {'name': 'Blue Bottle Coffee Beans', 'sku': 'FOD-BLB-CB-001', 'price': Decimal('24.99'), 'description': 'Premium single-origin coffee beans from Blue Bottle', 'stock': 50},
                    {'name': 'Teavana Jasmine Dragon Pearls', 'sku': 'FOD-TEA-JDP-002', 'price': Decimal('18.99'), 'description': 'Hand-rolled jasmine green tea pearls', 'stock': 40},
                    {'name': 'Lindt Swiss Chocolate Assortment', 'sku': 'FOD-LIN-SCA-003', 'price': Decimal('29.99'), 'description': 'Premium Swiss chocolate assortment box', 'stock': 60},
                    {'name': 'Artisanal Olive Oil Extra Virgin', 'sku': 'FOD-ART-OEV-004', 'price': Decimal('34.99'), 'description': 'Cold-pressed extra virgin olive oil from Tuscany', 'stock': 30},
                    {'name': 'Matcha Green Tea Powder', 'sku': 'FOD-MAT-GTP-005', 'price': Decimal('22.99'), 'description': 'Ceremonial grade matcha powder for traditional tea', 'stock': 35},
                    {'name': 'Belgian Dark Chocolate Truffles', 'sku': 'FOD-BEL-DCT-006', 'price': Decimal('19.99'), 'description': 'Handcrafted dark chocolate truffles from Belgium', 'stock': 45},
                    {'name': 'Organic Raw Honey', 'sku': 'FOD-ORG-RH-007', 'price': Decimal('16.99'), 'description': 'Pure organic raw honey from local beekeepers', 'stock': 55},
                    {'name': 'Craft Beer Variety Pack', 'sku': 'FOD-CRF-BVP-008', 'price': Decimal('39.99'), 'description': 'Selection of craft beers from local breweries', 'stock': 25},
                    {'name': 'Gourmet Sea Salt Collection', 'sku': 'FOD-GOU-SSC-009', 'price': Decimal('24.99'), 'description': 'Artisanal sea salts from around the world', 'stock': 40},
                    {'name': 'Premium Balsamic Vinegar', 'sku': 'FOD-PRE-BV-010', 'price': Decimal('28.99'), 'description': 'Aged balsamic vinegar from Modena, Italy', 'stock': 30}
                ]
            }
        ]

        # Create categories and products
        total_categories_created = 0
        total_products_created = 0

        for category_data in categories_data:
            # Create category
            category, category_created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            
            if category_created:
                total_categories_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

            # Create products for this category
            for product_data in category_data['products']:
                product, product_created = Product.objects.get_or_create(
                    sku=product_data['sku'],
                    defaults={
                        'name': product_data['name'],
                        'description': product_data['description'],
                        'price': product_data['price'],
                        'stock_quantity': product_data['stock'],
                        'category': category,
                        'is_active': True
                    }
                )
                
                if product_created:
                    total_products_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created product: {product.name} ({product.sku})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  Product already exists: {product.name} ({product.sku})')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {total_categories_created} new categories and {total_products_created} new products')
        )