from django.db import models

# Create your models here.
from django.conf import settings
from products.models import Product

class Sale(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="COMPLETED")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Sale {self.id} by {self.user.username}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.unit_price


class Payment(models.Model):
    """Payment model for tracking payment details"""
    PAYMENT_METHODS = [
        ("CASH", "Cash on Delivery"),
        ("CARD", "Credit/Debit Card"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ]

    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Payment reference number")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    processed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-processed_at']

    def __str__(self):
        return f"Payment for Sale {self.sale.id} - {self.get_method_display()} ({self.status})"