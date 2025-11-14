# Returns & Refunds (RMA) System Architectural Decision

## Status
**Accepted**

## Context

The retail management system requires a comprehensive returns and refunds system to handle customer return requests. The system needs to support:

- Customer-initiated return requests with item selection
- Multi-stage approval workflow with admin oversight
- Automatic refund calculations with restocking fees and shipping refunds
- Inventory restocking when items are returned
- Complete audit trail of all status changes
- Role-based access control (customers vs. administrators)
- Prevention of invalid status transitions
- Support for multiple resolution types (repair, replacement, refund)

Key requirements include:
- **Data Integrity**: Prevent invalid state transitions that could corrupt business logic
- **Auditability**: Complete history of who changed what and when
- **Financial Accuracy**: Precise refund calculations with fees and shipping
- **Inventory Management**: Automatic restocking when refunds are processed
- **User Experience**: Clear workflow for both customers and administrators
- **Business Rules**: Enforce complex workflow rules (e.g., can't refund before receiving items)

## Decision

We chose a **State Machine Pattern with Event Sourcing** for the RMA (Return Merchandise Authorization) system, implemented using Django models with explicit state transition methods.

### Technical Implementation

**Core Architecture:**
- **State Machine**: Explicit status transitions enforced by `can_transition_to()` and `transition_to()` methods
- **Event Logging**: Every status change recorded in `RMAEvent` model with actor, timestamp, and notes
- **Atomic Transactions**: All state changes wrapped in Django's `transaction.atomic()` for data integrity
- **Integrated Business Logic**: Refund calculation and inventory restocking built into model methods

**Key Components:**

1. **RMA Model** - Main return request entity with state machine logic:
```python
class RMA(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("under_review", "Under Review"),
        ("validated", "Validated"),
        ("in_transit", "In Transit"),
        ("received", "Received"),
        ("under_inspection", "Under Inspection"),
        ("approved", "Approved"),
        ("refunded", "Refunded"),
        ("closed", "Closed"),
        # ... additional statuses
    ]
    
    def can_transition_to(self, next_status):
        """Enforce valid status transitions"""
        valid_transitions = {
            "requested": ["under_review"],
            "under_review": ["validated", "declined"],
            "validated": ["in_transit", "declined"],
            "in_transit": ["received", "declined"],
            "received": ["under_inspection"],
            "under_inspection": ["approved", "declined"],
            "approved": ["repaired", "replaced", "refunded", "declined"],
            "refunded": ["closed"],
            "closed": [],  # Terminal state
        }
        return next_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status, actor=None, notes=""):
        """Transition to new status and log event"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.save()
        
        # Log the event
        RMAEvent.objects.create(
            rma=self,
            from_status=old_status,
            to_status=new_status,
            actor=actor or self.customer,
            notes=notes
        )
    
    def compute_refund_total(self):
        """Calculate refund total: subtotal - restocking_fee + shipping_refund"""
        subtotal = Decimal('0.00')
        for item in self.items.all():
            approved_qty = item.approved_quantity or item.requested_quantity
            subtotal += approved_qty * item.sale_item.unit_price
        return subtotal - self.restocking_fee + self.shipping_refund
```

2. **RMAEvent Model** - Event log for audit trail:
```python
class RMAEvent(models.Model):
    rma = models.ForeignKey(RMA, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

3. **RMAItem Model** - Individual items in return with approved vs. requested quantities:
```python
class RMAItem(models.Model):
    rma = models.ForeignKey(RMA, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT)
    requested_quantity = models.PositiveIntegerField()
    approved_quantity = models.PositiveIntegerField(null=True, blank=True)
```

4. **Atomic Transaction Wrapper** - All state changes use transactions:
```python
@transaction.atomic
def rma_refund(request, rma_id):
    rma = get_object_or_404(RMA, id=rma_id)
    rma.transition_to('refunded', actor=request.user, notes='Refund processed')
    
    # Restock inventory
    for item in rma.items.all():
        product = item.sale_item.product
        product.stock_quantity += item.approved_quantity
        product.save()
```

## Consequences

### Positive Consequences

- **Data Integrity**: State machine prevents invalid transitions, ensuring business rules are always enforced
- **Complete Audit Trail**: Every status change is logged with actor, timestamp, and notes for compliance and debugging
- **Business Logic Encapsulation**: State transition rules centralized in model methods, making changes easier
- **Type Safety**: Status choices defined as constants, preventing typos and invalid values
- **Testability**: State machine logic can be tested independently of views
- **Financial Accuracy**: Refund calculations built into model ensure consistency across all code paths
- **Inventory Consistency**: Automatic restocking integrated with refund processing prevents inventory discrepancies
- **User Experience**: Clear workflow states provide transparency to customers and administrators
- **Error Prevention**: Invalid transitions raise exceptions, preventing data corruption
- **Maintainability**: Workflow changes require updates in one place (transition rules)

### Negative Consequences

- **Complexity**: State machine logic adds complexity compared to simple status field updates
- **Performance Overhead**: Event logging creates additional database writes for each transition
- **Learning Curve**: Developers must understand state machine pattern and valid transitions
- **Rigidity**: Adding new statuses requires updating transition rules in multiple places
- **Database Growth**: Event log table grows over time (mitigated by archival strategies)
- **Code Duplication**: Transition validation logic exists in both model and potentially views
- **Testing Complexity**: Need to test all valid and invalid transition combinations

### Trade-offs

- **Data Integrity vs. Flexibility**: Chose strict state machine over flexible status updates for data integrity
- **Audit Trail vs. Performance**: Accepted additional database writes for complete auditability
- **Centralized Logic vs. Simplicity**: Prioritized centralized business logic over simpler implementation
- **Type Safety vs. Dynamic Behavior**: Chose static status choices over dynamic status management
- **Encapsulation vs. Direct Access**: Prefer model methods over direct field updates for safety

## Alternatives Considered

### Simple Status Field with View-Level Validation
- **Pros**: Simple implementation, direct field updates, minimal code
- **Cons**: No enforcement of valid transitions, easy to corrupt state, no audit trail
- **Decision**: Rejected due to lack of data integrity guarantees and auditability

### Workflow Engine (e.g., django-workflow, django-fsm)
- **Pros**: More powerful workflow capabilities, visual workflow design, advanced features
- **Cons**: Additional dependency, learning curve, overkill for current requirements
- **Decision**: Rejected due to added complexity and dependency for current needs

### Event Sourcing with Separate Event Store
- **Pros**: Complete event history, ability to replay events, advanced audit capabilities
- **Cons**: Significant complexity, separate event store infrastructure, performance overhead
- **Decision**: Rejected due to complexity and current requirements don't need full event sourcing

### Status Field with Database Constraints
- **Pros**: Database-level enforcement, simple implementation
- **Cons**: Limited expressiveness, hard to implement complex transition rules, no audit trail
- **Decision**: Rejected due to inability to enforce complex business rules and lack of auditability

### Hybrid Approach (State Machine + Optional Events)
- **Pros**: Flexibility to skip event logging for performance-critical paths
- **Cons**: Inconsistent audit trail, potential for missing important events
- **Decision**: Rejected due to need for complete auditability in financial operations

### Current Approach (State Machine + Event Logging)
- **Pros**: Data integrity, complete audit trail, centralized business logic, testable
- **Cons**: Additional complexity, performance overhead from event logging
- **Decision**: Accepted despite complexity due to superior data integrity and auditability

## Implementation Notes

### Status Workflow

The RMA workflow follows this progression:
1. **requested** → Auto-transitions to **under_review** on creation
2. **under_review** → Admin validates or declines
3. **validated** → Customer ships items (transitions to **in_transit**)
4. **in_transit** → Admin marks as **received**
5. **received** → Auto-transitions to **under_inspection**
6. **under_inspection** → Admin approves or declines
7. **approved** → Customer chooses resolution (repair/replacement/refund)
8. **refunded** → Admin processes refund and restocks inventory
9. **closed** → Terminal state

### Refund Calculation Formula

```
Refund Total = Subtotal - Restocking Fee + Shipping Refund

Where:
- Subtotal = Σ(approved_quantity × unit_price) for all RMA items
- Restocking Fee = Configurable fee (default: $0.00)
- Shipping Refund = Configurable refund amount (default: $0.00)
```

### Inventory Restocking

When RMA status transitions to "refunded":
- For each RMAItem, `product.stock_quantity` is increased by `approved_quantity`
- Restocking happens atomically within the same transaction as status change
- Prevents inventory discrepancies from partial refunds

### Event Logging

Every status transition creates an RMAEvent record with:
- `from_status`: Previous state
- `to_status`: New state
- `actor`: User who initiated the transition
- `timestamp`: When transition occurred
- `notes`: Optional notes about the transition

### Role-Based Access Control

- **Customers**: Can create RMAs, view their own RMAs, choose resolution type
- **Administrators**: Can view all RMAs, approve/decline, mark received, process refunds, close RMAs
- Access control enforced via `@admin_required` decorator and view-level checks

### Atomic Transactions

All state-changing operations use `@transaction.atomic()`:
- RMA creation with items and initial event
- Status transitions with event logging
- Refund processing with inventory restocking
- Ensures data consistency even if operations fail mid-process

### Testing Strategy

Tests cover:
- Valid status transitions
- Invalid transition prevention
- Refund calculation accuracy
- Inventory restocking on refund
- Event logging for all transitions
- Role-based access control
- Atomic transaction rollback on errors

## Related Decisions

- **Persistence ADR**: Uses Django ORM for all database operations
- **Database ADR**: SQLite/PostgreSQL for storing RMA data and events
- **Security ADR**: Role-based access control for admin functions
- **Business Rules ADR**: State machine enforces business rules at model level

This architectural decision provides a robust, auditable, and maintainable returns system that ensures data integrity while supporting complex business workflows.
