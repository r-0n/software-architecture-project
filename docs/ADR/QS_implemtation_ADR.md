# Architectural Decision Records (ADRs)

---

## ADR 1: Transactional Inventory Management with Row-Level Locking  
**Status:** Accepted  

### Context  
During flash sales, the system experiences high concurrent load (1000+ req/s) with limited stock. Without proper concurrency control, race conditions could lead to overselling, inventory inconsistencies, and customer dissatisfaction.

### Decision  
Implement atomic transactions with PostgreSQL row-level locking (`select_for_update`) for all inventory-modifying operations, combined with a stock reservation system during checkout.

### Consequences  
- **Positive:** Prevents overselling, maintains data consistency under high concurrency  
- **Negative:** Adds slight performance overhead due to locking  
- **Trade-offs:** Chose strong consistency over maximum throughput for inventory accuracy  

### Related Quality Scenarios  
- **A1:** Flash Sale Concurrency Control (Availability)  
- **P1:** Per-User+SKU Throttling (Performance)  
- **U1:** Specific Error Messages (Usability)  

### Evidence  
- `src/cart/views.py:459` – `with transaction.atomic():`  
- `src/cart/views.py:479` – `Product.objects.select_for_update(of=['self']).get()`  
- `tests/test_order_processing_robustness.py:353` – Stock conflict rollback tests  

---

## ADR 2: Resilient Payment Service Integration Pattern  
**Status:** Accepted  

### Context  
External payment gateways are critical dependencies that can fail, timeout, or become overloaded. Payment failures directly impact revenue and customer experience during high-volume events like flash sales.

### Decision  
Implement a comprehensive resilience pattern including:  
- Retry mechanism with exponential backoff and jitter  
- Circuit breaker to prevent cascading failures  
- Timeout handling with graceful degradation  
- Fast-fail when circuit is open  

### Consequences  
- **Positive:** Maintains system availability during payment service outages  
- **Negative:** Increased complexity in payment processing logic  
- **Trade-offs:** Accepted complexity for improved availability and user experience  

### Related Quality Scenarios  
- **A2:** Payment Service Resilience (Availability)  
- **U2:** Payment Unavailable UX (Usability)  
- **T1:** Dependency Injection & Mocking (Testability)  

### Evidence  
- `src/payments/service.py:64-116` – Retry with exponential backoff  
- `src/payments/service.py:46-59` – Circuit breaker fast-fail logic  
- `tests/test_order_processing_robustness.py:483` – Circuit breaker tests  

---

## ADR 3: Adapter Pattern for Partner Feed Integration  
**Status:** Accepted  

### Context  
The system needs to integrate with multiple partners providing product data in various formats (CSV, JSON) with evolving schemas. Hard-coding format handling would make the system brittle and difficult to maintain.

### Decision  
Implement the Adapter Pattern with a Factory to handle different feed formats. This provides:  
- Clear interface segregation (`FeedAdapter` ABC)  
- Easy extension for new formats  
- Centralized format detection and routing  
- Consistent validation and transformation pipeline  

### Consequences  
- **Positive:** High modifiability — new formats added without core changes  
- **Negative:** Additional abstraction layer complexity  
- **Trade-offs:** Chose flexibility over simplicity for long-term maintainability  

### Related Quality Scenarios  
- **M1:** Partner Feed Adapter Pattern (Modifiability)  
- **I1:** Validate → Transform → Upsert Pipeline (Integrability)  
- **I2:** Bulk Upsert Operations (Integrability)  

### Evidence  
- `src/partner_feeds/adapters.py:7-10` – `FeedAdapter` interface  
- `src/partner_feeds/adapters.py:23-30` – `FeedAdapterFactory`  
- `src/partner_feeds/services.py:28` – Dependency injection usage  

---

## ADR 4: Business Rules Separation Pattern  
**Status:** Accepted  

### Context  
Business rules for cart validation, pricing, and inventory management change frequently based on market conditions and business strategy. Mixing these rules with data access or presentation logic makes changes risky and time-consuming.

### Decision  
Extract all business rules into a dedicated `business_rules.py` module that:  
- Isolates volatile business logic from stable infrastructure code  
- Provides single responsibility for business policy enforcement  
- Enables comprehensive testing of business logic in isolation  
- Follows Domain-Driven Design (DDD) principles  

### Consequences  
- **Positive:** High modifiability — business changes require minimal code changes  
- **Negative:** Additional file organization overhead  
- **Trade-offs:** Separated concerns over co-location for maintainability  

### Related Quality Scenarios  
- **M2:** Business Rules Isolation (Modifiability)  
- **T1:** Dependency Injection & Mocking (Testability)  
- **T2:** Deterministic Test Environment (Testability)  

### Evidence  
- `src/cart/business_rules.py:9` – `validate_product_for_cart()`  
- `src/cart/business_rules.py:70` – `calculate_cart_total()`  
- `tests/test_business_logic.py:20` – Isolated business rule tests  

---

## ADR 5: Granular Throttling with Async Processing Split  
**Status:** Accepted  

### Context  
Flash sales generate extreme load that could overwhelm the system. Naive throttling approaches either block legitimate users or fail to prevent abuse. Additionally, mixing fast and slow operations in request-response cycles creates unpredictable latency.

### Decision  
Implement a multi-layered approach:  
- Per-user + SKU throttling to prevent individual abuse  
- `Retry-After` headers for clear user communication  
- Async queue split to separate fast sync operations from background processing  
- Cache-based rate limiting for performance  

### Consequences  
- **Positive:** Predictable performance under load, fair access distribution  
- **Negative:** Increased system complexity with queue management  
- **Trade-offs:** Chose bounded latency over simplicity for user experience  

### Related Quality Scenarios  
- **P1:** Per-User+SKU Throttling (Performance)  
- **P2:** Async Queue Split (Performance)  
- **U1:** Specific Error Messages (Usability)  

### Evidence  
- `src/cart/throttle.py:34-42` – Product-specific throttling  
- `src/cart/views.py:508` – Background job queuing  
- `src/cart/views.py:433-437` – `Retry-After` headers  

---

## ADR 6: Security-First Request Processing  
**Status:** Accepted  

### Context  
The system handles sensitive customer data, payment information, and partner integrations. Security breaches could lead to data loss, financial damage, and loss of customer trust.

### Decision  
Implement defense-in-depth security measures:  
- CSRF protection on all state-changing operations  
- Role-Based Access Control (RBAC) for admin functions  
- API key authentication for partner integrations  
- Input validation at multiple layers  

### Consequences  
- **Positive:** Comprehensive security coverage across attack vectors  
- **Negative:** Additional validation overhead on each request  
- **Trade-offs:** Chose security over performance for sensitive operations  

### Related Quality Scenarios  
- **S1:** CSRF Protection on Flash Checkout (Security)  
- **S2:** RBAC Authorization (Security)  
- **I1:** Validate → Transform → Upsert Pipeline (Integrability)  

### Evidence  
- `src/cart/views.py:362` – `@csrf_protect` decorator  
- `src/accounts/decorators.py:14-16` – Authentication checks  
- `src/partner_feeds/views.py:15` – API key authentication  

---

## ADR 7: User-Centered Error Handling and Communication  
**Status:** Accepted  

### Context  
During system stress or failures, unclear error messages frustrate users and increase support load. Technical error messages don't help end users resolve issues.

### Decision  
Implement user-centered error handling that:  
- Provides clear, actionable error messages  
- Maintains user context during failures  
- Offers specific guidance for resolution  
- Uses appropriate HTTP status codes and `Retry-After` headers  

### Consequences  
- **Positive:** Improved user experience during failure scenarios  
- **Negative:** Additional message formatting logic  
- **Trade-offs:** Chose user comprehension over technical accuracy in UI messages  

### Related Quality Scenarios  
- **U1:** Specific Error Messages (Usability)  
- **U2:** Payment Unavailable UX (Usability)  
- **A2:** Payment Service Resilience (Availability)  

### Evidence  
- `src/cart/views.py:185-190` – Form error processing  
- `src/cart/views.py:176` – Clear cart empty message  
- `src/cart/throttle.py:32` – User-friendly throttling messages  

---

## ADR 8: Comprehensive Test Strategy with Dependency Isolation  
**Status:** Accepted  

### Context  
Testing complex systems with external dependencies is challenging. Flaky tests, external service dependencies, and unpredictable test environments reduce development velocity and confidence.

### Decision  
Implement a test strategy emphasizing:  
- Strategic mocking of external dependencies  
- Deterministic test environments with controlled state  
- Dependency injection for testability  
- Comprehensive test coverage of failure scenarios  

### Consequences  
- **Positive:** Reliable, fast test execution; comprehensive failure testing  
- **Negative:** Test maintenance overhead; mock complexity  
- **Trade-offs:** Chose test reliability over test simplicity  

### Related Quality Scenarios  
- **T1:** Dependency Injection & Mocking (Testability)  
- **T2:** Deterministic Test Environment (Testability)  
- **A2:** Payment Service Resilience (Availability)  

### Evidence  
- `tests/test_order_processing_robustness.py:27` – Mock imports  
- `tests/test_order_processing_robustness.py:464` – Strategic mocking  
- `tests/test_order_processing_robustness.py:35` – Cache state management  

---

## Summary of Advantages  

- Reflects real architecture where decisions affect multiple quality attributes  
- Reduces duplication and promotes consistency across scenarios  
- Improves traceability between design decisions and quality attributes  
- Simplifies maintenance and future architectural evolution  
- Focuses documentation on key architectural concerns  

---

# Quality Scenarios and Architectural Decision Record (ADR) Mapping

This table maps each quality scenario from the Quality Attribute Catalog to the corresponding architectural tactic and ADR that addresses it.



| **Quality Attribute** | **Scenario ID** | **Tactic / Pattern Implemented** | **Corresponding ADR** |
|------------------------|----------------|----------------------------------|------------------------|
| **Availability** | A1 | Transactional Inventory Management (Row-Level Locking) | [ADR 1 – Transactional Inventory Management with Row-Level Locking](#adr-1-transactional-inventory-management-with-row-level-locking) |
| **Availability** | A2 | Resilient Payment Service Integration (Circuit Breaker + Retry + Timeout) | [ADR 2 – Resilient Payment Service Integration Pattern](#adr-2-resilient-payment-service-integration-pattern) |
| **Security** | S1 | CSRF Protection on Flash Checkout | [ADR 6 – Security-First Request Processing](#adr-6-security-first-request-processing) |
| **Security** | S2 | RBAC Authorization | [ADR 6 – Security-First Request Processing](#adr-6-security-first-request-processing) |
| **Modifiability** | M1 | Partner Feed Adapter Pattern | [ADR 3 – Adapter Pattern for Partner Feed Integration](#adr-3-adapter-pattern-for-partner-feed-integration) |
| **Modifiability** | M2 | Business Rules Separation Pattern | [ADR 4 – Business Rules Separation Pattern](#adr-4-business-rules-separation-pattern) |
| **Performance** | P1 | Per-User + SKU Throttling | [ADR 5 – Granular Throttling with Async Processing Split](#adr-5-granular-throttling-with-async-processing-split) |
| **Performance** | P2 | Async Queue Split | [ADR 5 – Granular Throttling with Async Processing Split](#adr-5-granular-throttling-with-async-processing-split) |
| **Integrability** | I1 | Validate → Transform → Upsert Pipeline | [ADR 3 – Adapter Pattern for Partner Feed Integration](#adr-3-adapter-pattern-for-partner-feed-integration) |
| **Integrability** | I2 | Bulk Upsert Operations | [ADR 3 – Adapter Pattern for Partner Feed Integration](#adr-3-adapter-pattern-for-partner-feed-integration) |
| **Testability** | T1 | Dependency Injection & Mocking | [ADR 8 – Comprehensive Test Strategy with Dependency Isolation](#adr-8-comprehensive-test-strategy-with-dependency-isolation) |
| **Testability** | T2 | Deterministic Test Environment | [ADR 8 – Comprehensive Test Strategy with Dependency Isolation](#adr-8-comprehensive-test-strategy-with-dependency-isolation) |
| **Usability** | U1 | Specific Error Messages | [ADR 7 – User-Centered Error Handling and Communication](#adr-7-user-centered-error-handling-and-communication) |
| **Usability** | U2 | Payment Unavailable UX | [ADR 7 – User-Centered Error Handling and Communication](#adr-7-user-centered-error-handling-and-communication) |

---

## ADR Index  

1. [ADR 1 – Transactional Inventory Management with Row-Level Locking](#adr-1-transactional-inventory-management-with-row-level-locking)  
2. [ADR 2 – Resilient Payment Service Integration Pattern](#adr-2-resilient-payment-service-integration-pattern)  
3. [ADR 3 – Adapter Pattern for Partner Feed Integration](#adr-3-adapter-pattern-for-partner-feed-integration)  
4. [ADR 4 – Business Rules Separation Pattern](#adr-4-business-rules-separation-pattern)  
5. [ADR 5 – Granular Throttling with Async Processing Split](#adr-5-granular-throttling-with-async-processing-split)  
6. [ADR 6 – Security-First Request Processing](#adr-6-security-first-request-processing)  
7. [ADR 7 – User-Centered Error Handling and Communication](#adr-7-user-centered-error-handling-and-communication)  
8. [ADR 8 – Comprehensive Test Strategy with Dependency Isolation](#adr-8-comprehensive-test-strategy-with-dependency-isolation)


---

> **Note:**
> Each ADR file documents the rationale, alternatives, and implementation details for the corresponding architectural tactic addressing its associated quality attribute(s).
