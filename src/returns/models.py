from django.db import models
from django.conf import settings
from orders.models import Sale, SaleItem
from products.models import Product
from decimal import Decimal


class RMA(models.Model):
    """Return Merchandise Authorization model"""
    
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("under_review", "Under Review"),
        ("validated", "Validated"),
        ("request_cancelled", "Request Cancelled"),
        ("in_transit", "In Transit"),
        ("received", "Received"),
        ("under_inspection", "Under Inspection"),
        ("approved", "Approved"),
        ("repaired", "Repaired"),
        ("replaced", "Replaced"),
        ("refunded", "Refunded"),
        ("declined", "Declined"),
        ("closed", "Closed"),
    ]
    
    RESOLUTION_CHOICES = [
        ("repair", "Repair"),
        ("replacement", "Replacement"),
        ("refund", "Refund"),
    ]
    
    REASON_CHOICES = [
        ("defective", "Defective/Damaged"),
        ("wrong_item", "Wrong Item Received"),
        ("not_as_described", "Not as Described"),
        ("changed_mind", "Changed Mind"),
        ("other", "Other"),
    ]
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="rmas")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rmas")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, blank=True, null=True, help_text="Customer's choice: Repair, Replacement, or Refund")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Customer notes or staff inspection notes")
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Return shipment tracking number")
    restocking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Restocking fee amount")
    shipping_refund = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Shipping refund amount")
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = "RMA"
        verbose_name_plural = "RMAs"
    
    def __str__(self):
        return f"RMA #{self.id} - Sale #{self.sale.id} - {self.get_status_display()}"
    
    def can_transition_to(self, next_status):
        """Enforce valid status transitions"""
        valid_transitions = {
            "requested": ["under_review"],  # Auto-transition on creation
            "under_review": ["validated", "declined"],  # Admin can validate or decline
            "validated": ["request_cancelled", "in_transit", "declined"],  # User can cancel or return, admin can decline
            "request_cancelled": [],  # Terminal state
            "in_transit": ["received", "declined"],  # Admin can mark received or decline
            "received": ["under_inspection"],  # Auto-transition after received
            "under_inspection": ["approved", "declined"],  # Admin can approve or decline
            "approved": ["repaired", "replaced", "refunded", "declined"],  # User chooses repair/replacement/refund, or admin can decline
            "repaired": ["closed"],  # Terminal state (can be closed)
            "replaced": ["closed"],  # Terminal state (can be closed)
            "refunded": ["closed"],  # Admin can close
            "declined": [],  # Terminal state
            "closed": [],  # Terminal state
        }
        return next_status in valid_transitions.get(self.status, [])
    
    def compute_refund_total(self):
        """Calculate refund total: subtotal - restocking_fee + shipping_refund"""
        subtotal = Decimal('0.00')
        for item in self.items.all():
            approved_qty = item.approved_quantity or item.requested_quantity
            subtotal += approved_qty * item.sale_item.unit_price
        
        return subtotal - self.restocking_fee + self.shipping_refund
    
    def get_current_status_display(self):
        """Get human-readable status"""
        return self.get_status_display()
    
    def transition_to(self, new_status, actor=None, notes=""):
        """Transition to new status and log event"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        
        if new_status in ["closed", "declined"] and not self.closed_at:
            from django.utils import timezone
            self.closed_at = timezone.now()
        
        self.save()
        
        # Log the event
        RMAEvent.objects.create(
            rma=self,
            from_status=old_status,
            to_status=new_status,
            actor=actor or self.customer,
            notes=notes
        )


class RMAItem(models.Model):
    """Individual items being returned in an RMA"""
    
    rma = models.ForeignKey(RMA, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT, related_name="rma_items")
    requested_quantity = models.PositiveIntegerField(help_text="Quantity customer requested to return")
    approved_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Quantity approved for return (set by staff)")
    
    class Meta:
        unique_together = [['rma', 'sale_item']]
    
    def __str__(self):
        return f"RMA #{self.rma.id} - {self.sale_item.product.name} (Qty: {self.approved_quantity or self.requested_quantity})"
    
    def get_refund_amount(self):
        """Calculate refund amount for this item"""
        qty = self.approved_quantity or self.requested_quantity
        return qty * self.sale_item.unit_price


class RMAEvent(models.Model):
    """Log of RMA status changes and events"""
    
    rma = models.ForeignKey(RMA, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="rma_events")
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"RMA #{self.rma.id}: {self.from_status} → {self.to_status} by {self.actor.username if self.actor else 'System'}"

