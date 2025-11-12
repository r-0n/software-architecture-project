# Returns & Refunds (RMA) Feature

Return Merchandise Authorization system for processing customer returns with automated refunds and inventory restocking.

## Features

- Customer return request creation
- Status workflow: requested → approved → received → refunded → closed
- Automatic refund calculation and inventory restocking
- Event logging with timestamps
- Admin actions (approve, receive, refund, close)
- Photo uploads and tracking numbers

## Status Workflow

1. **requested** → `approved`, `closed`
2. **approved** → `received`, `closed`
3. **received** → `refunded`, `closed`
4. **refunded** → `closed`
5. **closed** → terminal state

## Models

**RMA**: Main return request model
- Fields: `sale`, `customer`, `status`, `reason`, `opened_at`, `closed_at`, `notes`, `tracking_number`, `restocking_fee`, `shipping_refund`
- Methods: `compute_refund_total()`, `can_transition_to()`, `transition_to()`

**RMAItem**: Individual items in a return
- Fields: `rma`, `sale_item`, `requested_quantity`, `approved_quantity`
- Methods: `get_refund_amount()`

**RMAEvent**: Event log for status changes
- Fields: `rma`, `from_status`, `to_status`, `actor`, `timestamp`, `notes`

## Refund Calculation

```
Refund Total = Subtotal - Restocking Fee + Shipping Refund
```

Where Subtotal = Sum of (approved_quantity × unit_price) for all RMA items.

## Inventory Management

When RMA status transitions to "refunded", product `stock_quantity` is increased by `approved_quantity` for each RMAItem.

## URLs

- `/returns/` - List RMAs (filtered by role)
- `/returns/create/<sale_id>/` - Create RMA
- `/returns/<rma_id>/` - View RMA details
- `/returns/<rma_id>/approve/` - Approve (admin, POST)
- `/returns/<rma_id>/receive/` - Mark received (admin, POST)
- `/returns/<rma_id>/refund/` - Process refund (admin, POST)
- `/returns/<rma_id>/close/` - Close RMA (admin, POST)

## Testing

### Automated Tests

Run with:
```bash
cd src
python manage.py test returns
```

Tests cover: RMA creation, status transitions, refund calculations, inventory restocking, event logging.

### Manual Testing

**Prerequisites:**
- Server running (`python manage.py runserver`)
- Consumer and admin users created
- Migrations applied: `python manage.py makemigrations returns && python manage.py migrate`

**Customer Workflow:**
1. Login as consumer → View order details → Click "Return Items"
2. Select quantities, reason, optional notes/photo → Submit
3. Verify RMA created with "Requested" status

**Admin Workflow:**
1. Login as admin → View `/returns/` → Click "View Details"
2. Approve → Mark as Received → Process Refund → Close
3. Verify inventory restocked after refund

**Edge Cases:**
- Invalid status transitions (should fail)
- Multiple items, partial quantities
- Refund calculation with fees

## Troubleshooting

**"Return Items" button not showing:** Verify logged in as order owner, order exists with items.

**Cannot approve/receive/refund:** Check admin role in UserProfile, verify RMA status allows transition.

**Inventory not restocking:** Confirm refund action succeeded, check product stock quantity.

**RMA list empty:** Verify RMA created, check user role (admin sees all, customer sees own).

## Technical Details

**Views:** `create_rma`, `rma_list`, `rma_detail`, `rma_approve`, `rma_receive`, `rma_refund`, `rma_close`

**Forms:** `CreateRMAForm`, `RMAUpdateForm`

**Templates:** `returns_create.html`, `returns_list.html`, `returns_detail.html`

**Integration:** "Return Items" button in `templates/orders/order_detail.html`, models registered in Django admin.
