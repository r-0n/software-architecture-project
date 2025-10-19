# Quality Scenario Catalog — Checkpoint 2

Each scenario will follow the 6-part format as noted in the Checkpoint2 Document:
(Source, Stimulus, Environment, Artifact, Response, Response Measure)

---
## 1. Availability
### Scenario A1 — Graceful Degradation During Flash Sale
- **Source:** Multiple customers (1000 req/s)
- **Stimulus:** Surge in checkout requests
- **Environment:** Flash-Sale window active
- **Artifact:** Order Processing Service
- **Response:** Queue excess requests; serve queued orders in FIFO batches
- **Response Measure:** 95 % of orders confirmed ≤ 3 s; no crash

---
# Quality Scenarios from Previous assignment (not related to the current new feature implementations)
## 1. Availability

### Scenario A1 — Database Transaction Integrity
- **Source:** Concurrent users during checkout process
- **Stimulus:** Multiple users attempting to purchase the same limited stock item simultaneously
- **Environment:** Normal operation with concurrent database access
- **Artifact:** Shopping cart checkout system
- **Response:** System prevents overselling through atomic transactions and row-level locking, ensuring data consistency
- **Response Measure:** Zero overselling incidents, transaction rollback on conflicts, stock accuracy maintained 100%
- **Tactic/Pattern(s):** Atomic transactions, Row-level locking (select_for_update), Transaction rollback
- **Evidence:** 
  - `src/cart/views.py:174` — `with transaction.atomic():` implements ACID compliance
  - `src/cart/views.py:194` — `Product.objects.select_for_update().get()` prevents concurrent modifications
  - `tests/test_database_integration.py:460` — Atomic transaction testing validates behavior

### Scenario A2 — Graceful Error Recovery
- **Source:** System users during payment processing and cart operations
- **Stimulus:** Payment failures, stock conflicts, or system errors during checkout
- **Environment:** Normal operation with potential external service failures
- **Artifact:** Checkout and payment processing system
- **Response:** System provides clear error messages, maintains data consistency, and allows user recovery
- **Response Measure:** User receives actionable feedback within 2 seconds, system state remains consistent, error recovery rate > 95%
- **Tactic/Pattern(s):** Error boundary, Graceful degradation, User-friendly error messages
- **Evidence:** 
  - `src/cart/views.py:215` — `except IntegrityError as e:` implements error boundary
  - `src/cart/views.py:240` — Detailed user messages with cart clearing for recovery
  - `src/retail/payment.py:14` — Payment validation with specific error responses

---

## 2. Security

### Scenario S1 — Authentication and Authorization
- **Source:** System users attempting to access protected resources
- **Stimulus:** Unauthorized access attempts to admin functions or user-specific data
- **Environment:** Normal operation with mixed user roles (customer/admin)
- **Artifact:** User authentication and authorization system
- **Response:** System validates user credentials and enforces role-based access control
- **Response Measure:** Unauthorized access attempts blocked 100%, admin functions protected, session security maintained
- **Tactic/Pattern(s):** Authentication middleware, Role-based access control (RBAC), CSRF protection
- **Evidence:** 
  - `src/accounts/decorators.py:6` — `@admin_required` decorator implements RBAC
  - `src/accounts/views.py:51` — `@login_required` decorator enforces authentication
  - `src/retail/settings.py:60` — `'django.middleware.csrf.CsrfViewMiddleware'` prevents CSRF attacks

### Scenario S2 — Input Validation and Sanitization
- **Source:** System users submitting data through forms and APIs
- **Stimulus:** Malicious or invalid input data (SQL injection, XSS, invalid formats)
- **Environment:** Normal operation with user input processing
- **Artifact:** All user input interfaces (forms, APIs, cart operations)
- **Response:** System validates and sanitizes all input before processing, preventing security vulnerabilities
- **Response Measure:** Invalid input rejection rate 100%, no security vulnerabilities from input, validation errors < 1%
- **Tactic/Pattern(s):** Input validation, Form validation, Business rule validation, SQL injection prevention
- **Evidence:** 
  - `src/accounts/forms.py:24` — `def clean_email(self):` implements input validation
  - `src/retail/payment.py:18` — Card number validation prevents invalid data
  - `src/cart/business_rules.py:23` — Product validation enforces business rules

---

## 3. Modifiability

### Scenario M1 — Adapter Pattern for External Integration
- **Source:** External partner systems with different data formats
- **Stimulus:** Changes in partner feed formats (CSV to JSON, new field requirements)
- **Environment:** Partner integration with varying data formats
- **Artifact:** Partner feed ingestion system
- **Response:** System adapts to different feed formats without code changes through adapter pattern
- **Response Measure:** New format support added in < 1 day, zero code changes to core system, adapter reuse > 80%
- **Tactic/Pattern(s):** Adapter pattern, Factory pattern, Interface segregation, Dependency inversion
- **Evidence:** 
  - `src/partner_feeds/adapters.py:7` — `class FeedAdapter(ABC):` defines adapter interface
  - `src/partner_feeds/adapters.py:23` — `class FeedAdapterFactory:` implements factory pattern
  - `src/partner_feeds/services.py:27` — `adapter = FeedAdapterFactory.get_adapter()` uses dependency injection

### Scenario M2 — Business Logic Separation
- **Source:** Business requirements changes (pricing rules, validation logic)
- **Stimulus:** Changes to cart validation rules, pricing calculations, or business policies
- **Environment:** Development and maintenance phases
- **Artifact:** Cart business logic and pricing system
- **Response:** Business rules can be modified without affecting data layer or user interface
- **Response Measure:** Business rule changes implemented in < 2 hours, zero impact on data layer, test coverage maintained > 90%
- **Tactic/Pattern(s):** Business logic separation, Domain-driven design, Single responsibility principle
- **Evidence:** 
  - `src/cart/business_rules.py:9` — `def validate_product_for_cart()` separates business logic
  - `src/cart/business_rules.py:70` — `def calculate_cart_total()` isolates pricing logic
  - `tests/test_business_logic.py:53` — Business logic tests separated from database tests

---

## 4. Performance

### Scenario P1 — Database Query Optimization
- **Source:** Users querying product catalog and performing searches
- **Stimulus:** High-frequency product lookups, category filtering, and search operations
- **Environment:** Normal operation with growing product catalog (1000+ products)
- **Artifact:** Product database queries and catalog system
- **Response:** System maintains fast query performance through strategic database indexing
- **Response Measure:** Product queries respond in < 100ms, category filters in < 50ms, search operations in < 200ms
- **Tactic/Pattern(s):** Database indexing, Query optimization, Lazy loading
- **Evidence:** 
  - `src/products/models.py:54` — `models.Index(fields=['sku'])` optimizes SKU lookups
  - `src/products/models.py:55` — `models.Index(fields=['category'])` optimizes category filtering
  - `src/products/models.py:56` — `models.Index(fields=['is_active'])` optimizes active product queries

### Scenario P2 — Hybrid Storage Strategy
- **Source:** Cart operations from both anonymous and authenticated users
- **Stimulus:** Frequent cart updates, additions, and removals
- **Environment:** Mixed user types with varying persistence requirements
- **Artifact:** Shopping cart system
- **Response:** System uses optimal storage method (session vs database) based on user authentication state
- **Response Measure:** Cart operations complete in < 50ms, session storage for anonymous users, database persistence for authenticated users
- **Tactic/Pattern(s):** Hybrid storage, Performance optimization, Session management
- **Evidence:** 
  - `src/cart/models.py:50` — Database storage for authenticated users
  - `src/cart/models.py:70` — Session storage for anonymous users
  - `docs/ADR/cart_storage_ADR.md:27` — Hybrid storage decision documented

---

## 5. Integrability

### Scenario I1 — Partner Feed Integration
- **Source:** External partner systems providing product data feeds
- **Stimulus:** Product feed updates from partners in various formats (CSV, JSON)
- **Environment:** Partner integration with scheduled and manual feed processing
- **Artifact:** Partner feed ingestion system
- **Response:** System processes partner feeds, validates data, and updates product catalog automatically
- **Response Measure:** Feed processing success rate > 95%, data validation accuracy > 99%, processing time < 5 minutes per feed
- **Tactic/Pattern(s):** External API integration, Feed processing, Data transformation, Validation
- **Evidence:** 
  - `src/partner_feeds/services.py:16` — `def ingest_feed()` implements feed processing
  - `src/partner_feeds/models.py:5` — `class Partner` manages partner configurations
  - `src/partner_feeds/validators.py` — Product feed validation ensures data quality

### Scenario I2 — REST API Integration
- **Source:** External systems and frontend applications
- **Stimulus:** API requests for product data, cart operations, and order management
- **Environment:** Web application with external system integration
- **Artifact:** REST API endpoints and serialization
- **Response:** System provides standardized REST API endpoints with proper serialization and error handling
- **Response Measure:** API response time < 200ms, proper HTTP status codes, JSON serialization accuracy 100%
- **Tactic/Pattern(s):** REST API, JSON serialization, HTTP status codes, CORS handling
- **Evidence:** 
  - `requirements.txt:6` — `djangorestframework` enables REST API capabilities
  - `requirements.txt:7` — `django-cors-headers` handles cross-origin requests
  - `src/cart/views.py:115` — `def cart_count(request):` provides API endpoint

---

## 6. Testability

### Scenario T1 — Dependency Injection for Testing
- **Source:** Development team during testing and quality assurance
- **Stimulus:** Need to test business logic in isolation without external dependencies
- **Environment:** Development and testing phases
- **Artifact:** Test suite and business logic components
- **Response:** System supports isolated testing through dependency injection and mocking
- **Response Measure:** Test isolation achieved 100%, mock coverage > 90%, test execution time < 30 seconds
- **Tactic/Pattern(s):** Dependency injection, Mock objects, Test isolation, Interface abstraction
- **Evidence:** 
  - `tests/test_business_logic.py:14` — `from unittest.mock import patch` enables mocking
  - `tests/test_business_logic.py:45` — `with patch('src.retail.payment.random')` demonstrates dependency injection
  - `tests/test_database_integration.py:9` — `from unittest.mock import Mock` supports test isolation

### Scenario T2 — Business Logic Testability
- **Source:** Development team verifying business rule correctness
- **Stimulus:** Changes to business logic requiring validation and regression testing
- **Environment:** Development and maintenance phases
- **Artifact:** Business logic components and test suites
- **Response:** System provides isolated testing of business rules without database dependencies
- **Response Measure:** Business logic test coverage > 90%, test execution time < 10 seconds, zero database dependencies in unit tests
- **Tactic/Pattern(s):** Test isolation, Business logic separation, Unit testing, Test fixtures
- **Evidence:** 
  - `tests/test_business_logic.py:20` — `class PaymentProcessingBusinessLogicTest(SimpleTestCase)` isolates business logic
  - `tests/test_business_logic.py:53` — `class CartBusinessRulesTest(SimpleTestCase)` tests business rules
  - `tests/test_business_logic.py:1` — "Tests core business rules in isolation without database dependencies"

---

## 7. Usability

### Scenario U1 — User-Friendly Error Messages
- **Source:** System users encountering errors or validation failures
- **Stimulus:** User errors, validation failures, or system exceptions during normal operation
- **Environment:** Normal operation with user interaction
- **Artifact:** User interface and error handling system
- **Response:** System provides clear, actionable error messages that guide user recovery
- **Response Measure:** User error resolution rate > 80%, error message clarity score > 4/5, user satisfaction > 90%
- **Tactic/Pattern(s):** User-friendly error messages, Clear feedback, Error recovery guidance
- **Evidence:** 
  - `src/cart/views.py:62` — Detailed stock availability messages with specific quantities
  - `src/cart/views.py:240` — Clear concurrency conflict messages with recovery instructions
  - `src/retail/payment.py:20` — Specific payment validation messages with correction guidance

### Scenario U2 — Intuitive User Flow Design
- **Source:** System users navigating through the application
- **Stimulus:** User interactions with product browsing, cart management, and checkout process
- **Environment:** Normal operation with user interface interaction
- **Artifact:** User interface and navigation system
- **Response:** System provides intuitive navigation, clear visual feedback, and seamless user experience
- **Response Measure:** Task completion rate > 95%, user navigation efficiency > 90%, user satisfaction > 85%
- **Tactic/Pattern(s):** Intuitive navigation, Visual feedback, Responsive design, User experience optimization
- **Evidence:** 
  - `src/retail/urls.py:21` — `def redirect_to_products(request)` provides intelligent routing
  - `src/cart/views.py:19` — `def cart_view(request)` displays clear cart summary
  - `src/accounts/views.py:38` — Success messages provide positive feedback

---