# Breathe ESG Data Models

This document describes the architectural details, schemas, and design patterns utilized in the database layer of the Breathe ESG Ingestor platform.

---

## 1. Dual RawRecord and NormalizedRecord Architecture

Enterprise ESG ingestion requires a system that is both **flexible** and **auditable**. To achieve this, we use a two-tiered database model design:

1. **`RawRecord`**: Stores the exact, unmodified payload parsed from the upload files as a JSONB object (`raw_payload`), along with parsing metadata (status, error messages, and row numbers).
2. **`NormalizedRecord`**: Links to `RawRecord` via a `ForeignKey` relationship. It stores the normalized, standardized representation of the emissions data (canonical quantities, units, locations, and time ranges).

### Benefits of this Design:
- **Immutable Provenance**: We never lose the original source context. The raw row payload remains exactly as it was received.
- **Traceable Transformations**: Analysts can inspect the raw source row side-by-side with the normalized record in the review drawer, ensuring full transparency.
- **Support for Splits**: A single raw utility bill spanning multiple calendar months can yield multiple `NormalizedRecord` entries (one per month) while referencing the same `RawRecord`.

---

## 2. Multi-Tenancy Enforcement

Multi-tenancy is enforced natively and transparently at every tier to prevent cross-tenant data leaks:

- **JWT Claims**: When users authenticate, their JWT token contains a `tenant_id` claim.
- **`TenantMiddleware`**: Decodes the token on every request and binds the active `Tenant` to an async-safe and thread-safe `contextvars` variable.
- **`TenantAwareManager` & QuerySet**: All models belonging to a tenant override their default manager. Calling `Model.objects.all()` automatically injects `.filter(tenant=current_tenant)` into the database query.
- **Bypass for Admins**: Platform Administrators (`role = 'PLATFORM_ADMIN'`) set a bypass context variable, allowing them to query across tenants for platform maintenance.

---

## 3. Scope Classification

Emissions are classified into scopes according to the greenhouse gas protocol:
- **`SCOPE_1` (Direct)**: Emissions from sources owned or controlled by the tenant (e.g. combustion of diesel, natural gas).
- **`SCOPE_2` (Indirect)**: Emissions from the generation of purchased energy (e.g. purchased electricity).
- **`SCOPE_3` (Value Chain)**: Emissions occurring in the value chain of the tenant (e.g. corporate flights, hotel nights, car rentals, goods procurement).

These are mapped automatically during ingestion, but the mapping is also stored in the database (`ScopeMapping` model) so Breathe ESG staff can customize mappings in the Django Admin panel.

---

## 4. Status State Machine

Emissions records progress through a strict, immutable state machine:
```
[PENDING_REVIEW] ──(Analyst Edit / Flag)──> [PENDING_REVIEW]
       │
   (Approve / Reject)
       │
       ▼
 [APPROVED / REJECTED] ──(Batch Sign-Off)──> [LOCKED] (Immutable)
```
- **`LOCKED`**: Once a batch is signed off, its records enter the `LOCKED` state. Database signals and ViewSet validation blocks any updates, deletions, or status transitions on locked records, preserving them for auditing.

---

## 5. Precise Datatypes

- **`DecimalField`**: All quantity and distance values use `DecimalField(max_digits=20, decimal_places=6)`. We **never** use `FloatField` because binary floating-point representation introduces rounding errors (e.g. `0.1 + 0.2 != 0.3`). Precise floating-point arithmetic is a regulatory requirement in carbon accounting.
- **`JSONB`**: Used for `raw_payload` and `anomaly_flags`. JSONB allows indexing of JSON properties in PostgreSQL and supports fast schema-less queries.

---

## 6. Append-Only Audit Logs

The `AuditLog` table stores snapshots of batch actions and locked records.
- **Insert-Only Constraint**: It is configured as insert-only. Deletes or updates on this model are blocked at the application level.
- **State Snapshots**: When a record is locked, a complete JSON snapshot of its fields is written to the audit log, creating a permanent, cryptographically stable history for auditors.
