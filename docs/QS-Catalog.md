# Quality Scenario Catalog — Checkpoint 2

Each scenario will follow the 6-part format as noted in the Checkpoint2 Document:
(Source, Stimulus, Environment, Artifact, Response, Response Measure)

---
## 1. Availability

### Scenario A1 — Flash Sale Concurrency Control
- **Source:** Multiple users attempting flash sale checkout simultaneously
- **Stimulus:** High concurrent load during flash sale events (1000+ requests/second)
- **Environment:** Normal operation with flash sale enabled and limited stock
- **Artifact:** `src/cart/views.py::flash_checkout` (lines 459-490)
- **Response:** System prevents overselling through atomic transactions and row-level locking
- **Response-Measure:** 0 oversell incidents; stock consistency maintained under concurrent load; losing requests complete in <1s
- **Tactic/Pattern(s):** `transaction.atomic`, `select_for_update(of=['self'])`, stock reservation
- **Evidence:**
  - `src/cart/views.py:459` — `with transaction.atomic():` implements ACID compliance
  - `src/cart/views.py:479` — `Product.objects.select_for_update(of=['self']).get()` prevents race conditions
  - `tests/test_order_processing_robustness.py:353` — `test_stock_conflict_rollback` verifies rollback behavior

### Scenario A2 — Payment Service Resilience
- **Source:** External payment gateway failures and timeouts
- **Stimulus:** Payment service 5xx errors, timeouts, circuit breaker activation
- **Environment:** Normal operation with external payment dependencies
- **Artifact:** `src/payments/service.py::charge_with_resilience` (lines 20-133)
- **Response:** System maintains availability through retry, circuit breaker, and graceful degradation
- **Response-Measure:** ≥95% successful payments; <100ms fast-fail when circuit open; 0 payment data loss
- **Tactic/Pattern(s):** retry with exponential backoff, circuit breaker (OPEN/HALF_OPEN), timeout handling
- **Evidence:**
  - `src/payments/service.py:64-116` — retry loop with exponential backoff and jitter
  - `src/payments/service.py:46-59` — circuit breaker fast-fail logic
  - `tests/test_order_processing_robustness.py:483` — `test_circuit_breaker_short_circuit` verifies fast-fail

---

## 2. Security

### Scenario S1 — CSRF Protection on Flash Checkout
- **Source:** Malicious websites attempting cross-site request forgery attacks
- **Stimulus:** CSRF attacks targeting flash sale checkout endpoints
- **Environment:** Normal operation with CSRF middleware enabled
- **Artifact:** `src/cart/views.py::flash_checkout` (line 362)
- **Response:** System validates CSRF tokens and rejects forged requests
- **Response-Measure:** 100% CSRF attacks blocked; valid tokens required for all POST requests
- **Tactic/Pattern(s):** CSRF token validation, `@csrf_protect` decorator
- **Evidence:**
  - `src/cart/views.py:362` — `@csrf_protect` decorator enforces CSRF validation
  - `src/cart/views.py:5` — `from django.views.decorators.csrf import csrf_protect` import
  - `tests/test_order_processing_robustness.py:678` — `test_csrf_protection_on_flash_checkout` verifies 403 response

### Scenario S2 — RBAC Authorization
- **Source:** Users attempting to access admin functions and protected operations
- **Stimulus:** Unauthorized access attempts to admin functions, product management, partner feeds
- **Environment:** Normal operation with mixed user roles (customer/admin)
- **Artifact:** `src/accounts/decorators.py::admin_required` (lines 6-28)
- **Response:** System enforces role-based access control with proper redirects
- **Response-Measure:** 100% unauthorized access denied; proper redirects to login/admin pages
- **Tactic/Pattern(s):** `@admin_required` decorator, RBAC middleware, authentication checks
- **Evidence:**
  - `src/accounts/decorators.py:14-16` — authentication check with redirect to login
  - `src/accounts/decorators.py:22-25` — admin role validation with redirect
  - `src/products/views.py:92` — `@admin_required` applied to sensitive operations

---

## 3. Modifiability

### Scenario M1 — Partner Feed Adapter Pattern
- **Source:** External partner systems with different data formats and schemas
- **Stimulus:** Changes in partner feed formats (CSV to JSON, new field requirements, schema evolution)
- **Environment:** Partner integration with varying data formats and update frequencies
- **Artifact:** `src/partner_feeds/adapters.py::FeedAdapterFactory` (lines 23-30)
- **Response:** System adapts to different feed formats without core code changes through adapter pattern
- **Response-Measure:** New format support added in <1 day; zero core code changes; adapter reuse >80%
- **Tactic/Pattern(s):** adapter pattern, factory pattern, interface segregation
- **Evidence:**
  - `src/partner_feeds/adapters.py:7-10` — `class FeedAdapter(ABC):` defines adapter interface
  - `src/partner_feeds/adapters.py:23-30` — `class FeedAdapterFactory:` implements factory pattern
  - `src/partner_feeds/services.py:28` — `adapter = FeedAdapterFactory.get_adapter()` uses dependency injection

### Scenario M2 — Business Rules Isolation
- **Source:** Business requirements changes (pricing rules, validation logic, cart behavior)
- **Stimulus:** Changes to cart validation rules, pricing calculations, or business policies
- **Environment:** Development and maintenance phases with evolving business requirements
- **Artifact:** `src/cart/business_rules.py` (entire file)
- **Response:** Business rules can be modified without affecting data layer or user interface
- **Response-Measure:** Business rule changes implemented in <2 hours; zero impact on data layer; test coverage maintained >90%
- **Tactic/Pattern(s):** business rules separation, single responsibility principle, domain-driven design
- **Evidence:**
  - `src/cart/business_rules.py:9` — `def validate_product_for_cart()` separates validation logic
  - `src/cart/business_rules.py:70` — `def calculate_cart_total()` isolates pricing logic
  - `tests/test_business_logic.py:20` — `class CartBusinessRulesTest(SimpleTestCase)` tests business rules in isolation

---

## 4. Performance

### Scenario P1 — Per-User+SKU Throttling
- **Source:** Users attempting to abuse flash sale system with excessive requests
- **Stimulus:** High-frequency requests from individual users targeting specific products
- **Environment:** Flash sale events with high demand and limited stock
- **Artifact:** `src/cart/throttle.py::allow_checkout` (lines 11-63)
- **Response:** System implements granular throttling by user+product with Retry-After headers
- **Response-Measure:** p95 response time <1s; throttled requests return 429 with Retry-After; fair access maintained
- **Tactic/Pattern(s):** per-user+SKU throttling, Retry-After headers, cache-based rate limiting
- **Evidence:**
  - `src/cart/throttle.py:34-42` — product-specific throttling logic
  - `src/cart/throttle.py:32` — clear throttling message with retry time
  - `src/cart/views.py:433-437` — structured throttling response with Retry-After header

### Scenario P2 — Async Queue Split
- **Source:** Flash sale checkout requests requiring background processing
- **Stimulus:** High-volume checkout requests with payment processing and inventory updates
- **Environment:** Flash sale events with peak load and background processing requirements
- **Artifact:** `src/cart/views.py::flash_checkout` (lines 500-520)
- **Response:** System splits fast sync operations from background processing for bounded latency
- **Response-Measure:** Sync operations complete in <500ms; background jobs processed within 30s; queue depth <1000
- **Tactic/Pattern(s):** async queue split, background job processing, bounded latency
- **Evidence:**
  - `src/cart/views.py:508` — `job = enqueue_job('finalize_flash_order', job_payload)` queues background work
  - `src/cart/views.py:514-517` — sync duration measurement and logging
  - `src/worker/queue.py:64` — `def enqueue_job()` implements job queuing

---

## 5. Integrability

### Scenario I1 — Validate→Transform→Upsert Pipeline
- **Source:** External partner systems providing product data feeds in various formats
- **Stimulus:** Partner feed updates with validation requirements and data transformation needs
- **Environment:** Partner integration with scheduled and manual feed processing
- **Artifact:** `src/partner_feeds/services.py::_process_single_item` (lines 64-90)
- **Response:** System processes feeds through validate→transform→upsert pipeline with error isolation
- **Response-Measure:** ≥95% valid rows ingested; processing time <5 minutes per feed; error isolation maintained
- **Tactic/Pattern(s):** validate→transform→upsert pipeline, error isolation, data transformation
- **Evidence:**
  - `src/partner_feeds/services.py:66-69` — validation step with error handling
  - `src/partner_feeds/services.py:72` — `product_data = self.validator.transform_item()` transformation
  - `src/partner_feeds/services.py:86` — `Product.objects.update_or_create()` upsert operation

### Scenario I2 — Bulk Upsert Operations
- **Source:** Large partner feed files with thousands of products requiring efficient processing
- **Stimulus:** Bulk product ingestion and updates from partner systems
- **Environment:** Partner integration with large data volumes and performance requirements
- **Artifact:** `src/partner_feeds/services.py::ingest_feed` (lines 17-62)
- **Response:** System uses efficient bulk operations for data processing with batch error handling
- **Response-Measure:** 1000+ products processed in <30s; memory usage <100MB; batch error isolation
- **Tactic/Pattern(s):** `update_or_create`, `get_or_create`, batch processing, error isolation
- **Evidence:**
  - `src/partner_feeds/services.py:86` — `Product.objects.update_or_create()` for efficient upserts
  - `src/partner_feeds/services.py:76` — `Category.objects.get_or_create()` for category handling
  - `src/partner_feeds/services.py:36-45` — batch processing with individual error handling

---

## 6. Testability

### Scenario T1 — Dependency Injection & Mocking
- **Source:** Development team testing external service interactions and failure scenarios
- **Stimulus:** Need to test payment failures, circuit breaker behavior, retry logic without affecting real services
- **Environment:** Test environment with controlled external dependencies
- **Artifact:** `tests/test_order_processing_robustness.py:27` (mock imports and usage)
- **Response:** System uses strategic mocking to test external service interactions and failure scenarios
- **Response-Measure:** External service behavior testable; no real service calls in tests; mock coverage >90%
- **Tactic/Pattern(s):** mock objects, patch decorators, controlled test environments, dependency injection
- **Evidence:**
  - `tests/test_order_processing_robustness.py:27` — `from unittest.mock import patch, MagicMock` imports
  - `tests/test_order_processing_robustness.py:464` — `patch('payments.client.PaymentGateway.charge')` strategic mocking
  - `tests/test_order_processing_robustness.py:74-100` — comprehensive test scenarios with mocks

### Scenario T2 — Deterministic Test Environment
- **Source:** Development team requiring consistent test execution and reproducible results
- **Stimulus:** Test execution with controlled state, cache management, and deterministic behavior
- **Environment:** Test environment with isolated state and controlled dependencies
- **Artifact:** `tests/test_order_processing_robustness.py:30` (TransactionTestCase setup)
- **Response:** System provides deterministic test environment with controlled state and cache management
- **Response-Measure:** Test execution deterministic; cache state controlled; test isolation maintained
- **Tactic/Pattern(s):** deterministic test environment, cache management, test isolation, controlled state
- **Evidence:**
  - `tests/test_order_processing_robustness.py:30` — `class OrderProcessingRobustnessTest(TransactionTestCase)` for database testing
  - `tests/test_order_processing_robustness.py:35` — `cache.clear()` ensures clean state
  - `tests/test_order_processing_robustness.py:70` — `cache.clear()` cleanup after each test

---

## 7. Usability

### Scenario U1 — Specific Error Messages
- **Source:** Users encountering errors during normal operations (validation failures, stock conflicts, payment errors)
- **Stimulus:** User errors, validation failures, or system exceptions during cart and checkout operations
- **Environment:** Normal operation with user interactions and potential error conditions
- **Artifact:** `src/cart/views.py::checkout` (lines 182-196)
- **Response:** System provides clear, actionable error messages with emojis and specific guidance
- **Response-Measure:** Error messages <50 words; 90%+ user comprehension; actionable feedback provided
- **Tactic/Pattern(s):** user-friendly messaging, emoji indicators, actionable feedback, clear guidance
- **Evidence:**
  - `src/cart/views.py:185-190` — form error processing with HTML tag removal and clear messaging
  - `src/cart/views.py:176` — clear cart empty message with emoji: "⚠️ Your cart is empty."
  - `src/cart/views.py:232` — payment error message with emoji: "⚠️ Payment service error. Please try again."

### Scenario U2 — Payment Unavailable UX
- **Source:** Users experiencing payment service unavailability or circuit breaker activation
- **Stimulus:** Payment service failures, circuit breaker open state, or throttling during high load
- **Environment:** High-load operation with payment service issues or throttling active
- **Artifact:** `src/cart/views.py::checkout` (lines 280-310) and `src/payments/service.py::charge_with_resilience` (lines 46-73)
- **Response:** System provides clear guidance on payment unavailability with retry timing and no data loss
- **Response-Measure:** Payment unavailable messages <30 words; fallback shown within 1s; retry delay ≤5s; no data loss; user guidance clear
- **Tactic/Pattern(s):** payment unavailable UX, retry-after headers, clear guidance, no data loss, fast-fail timing
- **Evidence:**
  - `src/payments/service.py:47-60` — circuit breaker fast-fail with retry delay calculation (capped at 5s)
  - `src/cart/views.py:284-310` — fallback response time measurement and retry delay messaging
  - `src/cart/views.py:297-303` — fallback response time validation (logs error if >1s)
  - `src/cart/views.py:305-309` — user-facing message with retry timing (retry delay ≤5s)
