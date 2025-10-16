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

### Scenario A2 — Retry on Payment Service Failure