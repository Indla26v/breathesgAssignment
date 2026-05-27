# Architectural Decisions & Ambiguity Resolutions

This document logs the core engineering design decisions made during the development of the Breathe ESG Ingestor.

---

## 1. SAP Integration: Flat File over IDoc or OData
- **Decision**: Build a tab-delimited SE16 flat-file parser rather than OData/RFC API connectors.
- **Rationale**: Direct SAP OData integration requires configuring SAP Gateways, managing certificates, and negotiating corporate firewalls, which takes months of enterprise IT alignment. In contrast, SE16 or table exports (MSEG, EKPO) are the universal, lowest-common-denominator exports that finance and operations teams can extract immediately.

---

## 2. Utility Portals: CSV over API Polling
- **Decision**: Focus on CSV bill parsing instead of web scraper connectors.
- **Rationale**: Scrapers for utility portals (PG&E, Duke Energy) are notoriously fragile and break whenever frontends are updated. Batch uploading exported CSV bill portals is the standard, reliable practice for energy managers.

---

## 3. Concur Travel: CSV over API Integration
- **Decision**: Ingest Standard Detail Report CSV exports instead of OAuth2 API integrations.
- **Rationale**: Implementing full Concur OAuth2 connectors introduces token refreshes, rate-limiting, and credentials storage concerns. Real-world finance teams routinely export weekly travel reports as CSV, making batch uploads a natural fit.

---

## 4. Billing Period Splitting
- **Decision**: Proportions are allocated linearly by day count when a utility billing period spans multiple calendar months.
- **Rationale**: Corporate carbon footprints must align to calendar months for financial quarters. Splitting by day count (e.g. Sept 14 – Oct 13: 17 days in Sept, 13 days in Oct) is the widely accepted protocol in GHG accounting.

---

## 5. Unknown Plant Codes
- **Decision**: Ingest unknown plant codes, store them as `facility_id`, and raise an `UNKNOWN_FACILITY` flag instead of failing the parse.
- **Rationale**: If we rejected unknown plant codes, a single missing master data entry would block the ingestion of thousands of rows. Flagging allows the batch to proceed while highlighting the missing facility mapping for the analyst to correct.

---

## 6. Supported SAP Movement Types
- **Decision**: Standardize on movement types:
  - `201` / `261` (Goods Issue / Consumption) -> Scope 1 Combustion.
  - `101` / `501` (Goods Receipt / Procurement) -> Scope 3 Purchased Fuel.
- **Rationale**: These represent 90% of material inventory transitions related to direct consumption and procurement.

---

## 7. Great-Circle Distance Inference
- **Decision**: Use a local OpenFlights database (`airports.dat`) and the Haversine formula to compute distance in KM if not provided, setting `distance_inferred = True`.
- **Rationale**: External geocoding APIs introduces rate limits, network latency, and billing concerns. A local airport coordinate database is fast, reliable, and offline-compatible.

---

## 8. No Partial Sign-Offs
- **Decision**: Batches can only be signed off if **all** records are either `APPROVED` or `REJECTED`.
- **Rationale**: Partial sign-offs complicate reporting. All-or-nothing sign-off ensures that batches represent atomic, audited slices of time.
