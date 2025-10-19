from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for retail management system"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Add these new fields for partner integration and flash sales
    partner = models.ForeignKey('partner_feeds.Partner', on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='products')
    is_flash_sale = models.BooleanField(default=False)
    flash_sale_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    flash_sale_start = models.DateTimeField(null=True, blank=True)
    flash_sale_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['partner']),  # New index
            models.Index(fields=['is_flash_sale']),  # New index
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0

    @property
    def stock_status(self):
        """Get stock status as string"""
        if self.stock_quantity == 0:
            return "Out of Stock"
        elif self.stock_quantity <= 10:
            return "Low Stock"
        else:
            return "In Stock"
    
    @property
    def is_on_flash_sale(self):
        """Check if product is currently on flash sale"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_flash_sale and
            self.flash_sale_price is not None and
            self.flash_sale_start and
            self.flash_sale_end and
            self.flash_sale_start <= now <= self.flash_sale_end
        )
    
    @property
    def current_price(self):
        """Get current price (flash sale price if active, else regular price)"""
        return self.flash_sale_price if self.is_on_flash_sale else self.price