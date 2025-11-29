# CP4: Order History Filters, Low-Stock Configuration, and RMA Notifications

## Context

The assignment required three lightweight enhancements to the existing e-commerce architecture:

1. **Customer-side Order History filtering**: Status filters, date range, keyword search, and no-return-request filter
2. **Admin-side configurable low-stock threshold**: Dynamic threshold configuration for inventory alerts
3. **Lightweight RMA notifications**: Status progression display for return requests

The goal was to enhance user experience and administrative capabilities while maintaining the simplicity and maintainability of the current system.

Key requirements:
- Minimal code footprint and easy maintainability
- Reuse existing UI patterns for consistency
- No changes to deployment or infrastructure
- Server-side filtering using Django ORM
- Lightweight front-end notifications only (no email/SMS/WebSockets)

## Decision

We implemented all three features using Django's built-in server-side rendering and form handling, with minimal additions to the existing codebase. This approach maintains consistency with the existing architecture while providing the required functionality.

### Technical Implementation

All features follow the existing Django patterns:
- Server-side form handling with GET parameters
- Django ORM for database queries and filtering
- Template-based UI rendering with Bootstrap components
- Custom admin checks using `user_is_admin` context processor

### 1. Order History Filtering & Search (Feature 2.1)

**Implementation:**
- Added `OrderHistoryFilterForm` in `src/orders/forms.py` with fields: `search`, `status`, `start_date`, `end_date`, `only_no_returns`
- Enhanced `order_history` view in `src/orders/views.py` with:
  - Dynamic status filtering based on RMA status and resolution
  - Keyword search across order ID (numeric) and product names via related `SaleItem` relationships using Django `Q` objects
  - Date range filtering on `Sale.created_at` using `__date__gte` and `__date__lte`
  - `overall_status` computation that maps complex RMA workflow states into filterable categories:
    - **Refunded**: RMA status "refunded" or closed with `resolution='refund'`
    - **Pending**: RMA status in `["requested", "under_review", "validated", "in_transit"]`
    - **Returned**: RMA status in `["received", "under_inspection", "approved"]`
    - **Completed**: Terminal states like `request_cancelled`, `repaired`, `replaced`, `declined`, or `closed` (non-refund)
  - Special handling for "Completed" filter: shows paid orders that had return history (excludes clean orders with no returns)
  - "Only show orders with no return requests" checkbox filter (orthogonal to status filter)
- Filter UI in `src/templates/orders/order_history.html` matches the existing product search form design for consistency
- All filters work in combination and preserve state in URL GET parameters

**Key Design Choices:**
- Reused the existing `ProductSearchForm` pattern for UI consistency
- Used `overall_status` mapping to simplify complex RMA state machine into user-friendly categories
- Applied filters server-side using Django ORM for security and performance
- Special "Completed" filter logic ensures it shows only orders with return history (not clean orders)

### 2. Configurable Low-Stock Alerts (Feature 2.2)

**Implementation:**
- Added new setting `LOW_STOCK_THRESHOLD_DEFAULT` in `src/retail/settings.py`:
  - Default value: 10
  - Configurable via environment variable `LOW_STOCK_THRESHOLD_DEFAULT`
- Enhanced `product_list` view in `src/products/views.py` with:
  - Runtime threshold calculation from request GET parameters or default setting
  - Admin-only filter application when "only low stock" checkbox is checked
  - Filter: `stock_quantity__gt=0, stock_quantity__lte=threshold`
  - Uses custom `user_is_admin` logic (not Django's `is_staff`) to match existing admin checks
- Admin controls added to `src/templates/products/product_list.html`:
  - Threshold input field pre-filled with current threshold value
  - "Only show low-stock products (≤ threshold)" checkbox
  - Only visible when `user_is_admin` is True (same condition as "Add New Product" button)
- Regular customers see no changes to the UI

**Key Design Choices:**
- Environment-variable configuration for deployment flexibility
- Admin-only UI controls using existing `user_is_admin` context processor
- Server-side filtering preserves existing query optimization
- Threshold validation (non-negative, fallback on error)

### 3. Lightweight RMA Status Notifications (Feature 2.3)

**Implementation:**
- Status badges and notifications integrated into RMA detail and list views
- Uses existing Bootstrap badge components for consistent styling
- Displays simplified RMA workflow stages:
  - Submitted → Received → Under Inspection → Approved → Refunded
- No backend notification service required — lightweight front-end implementation only
- Integrated with existing Returns & Refunds workflow in `src/templates/returns/` templates

**Key Design Choices:**
- Front-end only notifications (no email/SMS/WebSockets)
- Reuses existing Bootstrap components for consistency
- Minimal code footprint with template-level implementation
- Clear visual indicators for RMA status at each stage

## Alternatives Considered

For all three features, the following alternatives were considered and rejected:

### 1. Building a React Frontend or Client-Side Filtering
**Rejected because:**
- Would require significant infrastructure changes
- Mismatch with existing Django server-rendered architecture
- Unnecessary complexity for the assignment scope
- Would break consistency with existing UI patterns

### 2. Adding New API Endpoints for Filtering/Searching
**Rejected because:**
- Existing Django views already handle GET parameters efficiently
- Server-side filtering provides better security and performance
- No need for separate API layer in current architecture
- Would add unnecessary abstraction

### 3. Using WebSockets or Asynchronous Notifications for RMA Events
**Rejected because:**
- Assignment specified "lightweight" notifications only
- Would require additional infrastructure (WebSocket server, message queue)
- Email/SMS services add external dependencies and complexity
- Front-end badges provide sufficient user feedback for the use case

### 4. Creating a Persistent Database-Backed Configuration Model for Thresholds
**Rejected because:**
- Environment variable configuration is simpler and sufficient
- No need for per-user or per-tenant threshold settings
- Database model would add unnecessary complexity
- Environment variable approach aligns with deployment best practices

### 5. Direct SQL Queries for Performance
**Rejected because:**
- Django ORM provides sufficient performance for current scale
- ORM queries are more maintainable and secure
- No performance issues identified that would justify raw SQL
- ORM abstraction protects against SQL injection

## Consequences

### Positive Consequences

1. **Clean Integration**: All features integrate seamlessly with existing Django architecture
   - No changes to deployment or infrastructure required
   - Consistent with existing code patterns and conventions
   - Minimal learning curve for developers familiar with the codebase

2. **Maintainability**: Minimal code footprint and easy to maintain
   - Reuses existing UI patterns (product search form)
   - Server-side filtering keeps business logic in one place
   - Clear separation of concerns (forms, views, templates)

3. **User Experience Improvements**:
   - **Customers**: Gain intuitive control over order history with multiple filter options
   - **Admins**: Real-time inventory insight via configurable low-stock thresholds
   - **All Users**: Clear RMA status progression through visual badges

4. **Performance**: Server-side filtering using Django ORM
   - Efficient database queries with proper indexing
   - No client-side JavaScript overhead
   - URL parameters enable bookmarkable filtered views

5. **Security**: Server-side validation and filtering
   - All filters validated on the server
   - No client-side manipulation of filter logic
   - Admin-only features properly gated by `user_is_admin` check

6. **Flexibility**: Environment-variable configuration for thresholds
   - Easy to adjust defaults per deployment environment
   - No code changes required for threshold updates
   - Follows 12-factor app principles

### Negative Consequences

1. **Static Thresholds in Templates**: Existing hard-coded thresholds (10, 5) in templates and model properties remain unchanged
   - Future enhancement could refactor these to use the configurable threshold
   - Current implementation focuses on admin-side dynamic filtering only

2. **No Real-Time Updates**: RMA notifications are template-based only
   - Users must refresh page to see status changes
   - No push notifications or live updates
   - Limited user engagement compared to real-time systems

3. **Server-Side Only**: All filtering happens on the server
   - Requires page reload for filter changes
   - No client-side instant filtering
   - Slightly slower user experience compared to client-side filtering

### Trade-offs

- **Simplicity vs. Richness**: Chose lightweight implementation over feature-rich alternatives (React, WebSockets)
- **Server-Side vs. Client-Side**: Prioritized security and consistency over instant filtering
- **Configuration vs. Flexibility**: Environment variables provide deployment flexibility without database complexity
- **Maintainability vs. Performance**: Accepted server-side filtering for better maintainability and security

## Implementation Notes

### Order History Filtering

The `overall_status` mapping simplifies the complex RMA state machine into user-friendly categories:

```python
# Status mapping logic in order_history view
if existing_rma:
    rma_status = existing_rma.status
    rma_resolution = getattr(existing_rma, "resolution", None)
    
    if rma_status == "refunded" or (rma_status == "closed" and rma_resolution == "refund"):
        overall_status = "refunded"
    elif rma_status in ["requested", "under_review", "validated", "in_transit"]:
        overall_status = "pending"
    elif rma_status in ["received", "under_inspection", "approved"]:
        overall_status = "returned"
    elif rma_status in ["request_cancelled", "repaired", "replaced", "declined", "closed"]:
        overall_status = "completed"
else:
    # Fallback to Sale.status when no RMA exists
    raw_status = (sale.status or "").lower()
    if raw_status in ["pending", "processing", "requested", "under_review"]:
        overall_status = "pending"
    else:
        overall_status = "completed"
```

The "Completed" filter has special logic to show only paid orders that had return history, excluding clean orders with no returns.

### Low-Stock Configuration

Threshold configuration uses environment variables with Django settings:

```python
# In src/retail/settings.py
LOW_STOCK_THRESHOLD_DEFAULT = int(os.environ.get("LOW_STOCK_THRESHOLD_DEFAULT", 10))

# In product_list view
try:
    threshold = int(request.GET.get("low_stock_threshold", settings.LOW_STOCK_THRESHOLD_DEFAULT))
    if threshold < 0:
        threshold = settings.LOW_STOCK_THRESHOLD_DEFAULT
except (TypeError, ValueError):
    threshold = settings.LOW_STOCK_THRESHOLD_DEFAULT
```

Admin check uses the custom `user_is_admin` logic (not Django's `is_staff`) to match existing admin controls:

```python
can_manage_products = False
if request.user.is_authenticated:
    if request.user.is_superuser:
        can_manage_products = True
    elif hasattr(request.user, 'profile'):
        can_manage_products = request.user.profile.is_admin
```

### RMA Status Notifications

Status badges use Bootstrap components for consistent styling:

```html
<!-- In RMA templates -->
<span class="badge bg-warning text-dark">In Process</span>
<span class="badge bg-success">Repaired</span>
<span class="badge bg-success">Refunded</span>
```

No backend notification service is required - all status display is template-based.

## Related Decisions

- **Persistence ADR**: Uses Django ORM for all database filtering operations
- **Returns Design ADR**: RMA status mapping leverages existing RMA state machine
- **Cart Storage ADR**: Follows same pattern of server-side form handling with GET parameters
- **Database ADR**: SQLite database supports all filtering queries efficiently

This architectural decision provides lightweight, maintainable enhancements that integrate seamlessly with the existing Django architecture while meeting the assignment requirements for minimal complexity and maximum consistency.
