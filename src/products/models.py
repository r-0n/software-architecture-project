from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
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
    
    # Partner integration
    partner = models.ForeignKey('partner_feeds.Partner', on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='products')
    
    # Enhanced flash sale fields with proper naming
    flash_sale_enabled = models.BooleanField(default=False)
    flash_sale_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    flash_sale_starts_at = models.DateTimeField(null=True, blank=True)
    flash_sale_ends_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['partner']),
            models.Index(fields=['flash_sale_enabled']),  # For efficient active sales listing
        ]
        constraints = [
            # Conditional constraint: only enforce when all flash fields are set and enabled
            models.CheckConstraint(
                check=models.Q(
                    # Either flash sale is disabled, OR all required fields are present
                    models.Q(flash_sale_enabled=False) |
                    models.Q(
                        flash_sale_enabled=True,
                        flash_sale_price__isnull=False,
                        flash_sale_starts_at__isnull=False,
                        flash_sale_ends_at__isnull=False,
                        flash_sale_starts_at__lt=models.F('flash_sale_ends_at')
                    )
                ),
                name='flash_sale_time_order'
            ),
        ]

    def clean(self):
        """Enhanced validation for flash sale fields"""
        super().clean()
        
        if self.flash_sale_enabled:
            if not self.flash_sale_price:
                raise ValidationError("Flash sale price is required when flash sale is enabled")
            if not self.flash_sale_starts_at:
                raise ValidationError("Flash sale start time is required when flash sale is enabled")
            if not self.flash_sale_ends_at:
                raise ValidationError("Flash sale end time is required when flash sale is enabled")
            if self.flash_sale_starts_at and self.flash_sale_ends_at and self.flash_sale_starts_at >= self.flash_sale_ends_at:
                raise ValidationError("Flash sale start time must be before end time")

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
            self.flash_sale_enabled and
            self.flash_sale_price is not None and
            self.flash_sale_starts_at and
            self.flash_sale_ends_at and
            self.flash_sale_starts_at <= now <= self.flash_sale_ends_at
        )
    
    @property
    def current_price(self):
        """Get current price (flash sale price if active, else regular price)"""
        return self.flash_sale_price if self.is_on_flash_sale else self.price