# ESGSync — Data Model Reference

## Multi-Tenancy Approach

ESGSync uses a **single-database, organization-scoped** multi-tenancy model.

Every domain model carries a `organization` FK. Query isolation is enforced:
1. At the middleware layer (`OrganizationContextMiddleware` binds `request.organization`)
2. At the view layer (all querysets filter by `organization=request.user.organization`)
3. JWT tokens embed `org_id` to prevent cross-tenant token reuse

No row-level security at the DB level was chosen because:
- Adds complexity without benefit in a single-app deployment
- Organization scoping in application code is auditable and testable
- Django ORM provides querysets that are easy to review

---

## Core Entity Relationships

```
Organization
  └── User (many, with role)
  └── DataSource (typed: SAP_FUEL | UTILITY | TRAVEL)
  └── Facility (physical locations)
  └── Vendor (procurement counterparties)
  └── UploadSession (file ingestion job)
       └── RawRecord (one per CSV row)
            └── ValidationError (per-field failures)
            └── EmissionRecord (created for non-failed rows)
                 └── ReviewTask (analyst workflow)
  └── AuditLog (immutable event stream)
```

---

## Ingestion Status Machine

```
UPLOADED
  → VALIDATING   (Celery task starts)
  → NORMALIZED   (all rows processed, EmissionRecords created)
  → FAILED       (unrecoverable parse/system error)

EmissionRecord states:
  REVIEW_PENDING → APPROVED   (analyst approves)
  REVIEW_PENDING → REJECTED   (analyst rejects, reason required)
  REJECTED       → REVIEW_PENDING (reopened)
  APPROVED       → LOCKED_FOR_AUDIT (auditor locks)
```

Valid transitions are enforced in `EmissionRecordService` — invalid transitions raise `InvalidWorkflowTransitionException`.

---

## Normalization Strategy

Raw CSV data is processed in three layers:

1. **Schema Mapping** (`SchemaMapper`): Column name aliases → canonical field names.
   Handles English, German SAP field names, abbreviations, and spacing variants.

2. **Transformation** (`SAPTransformer`, `UtilityTransformer`, `TravelTransformer`):
   Converts raw values to typed, canonical fields. Date parsing, unit normalization, emission factor application.

3. **Unit Conversion** (`UnitConverter`):
   - Volume → Liters (all volumetric fuels)
   - Mass → Kilograms
   - Energy → kWh
   - Distance → Kilometers
   All canonical units stored; original unit preserved in `unit_raw`.

Emission calculations happen at normalization time. Factors from IPCC AR5 and EPA.

---

## Audit Architecture

`AuditLog` is write-once. The model overrides `save()` and `delete()` to raise `RuntimeError` if called post-creation. This enforces immutability at the ORM layer.

Events logged:
- File uploads (who, when, source, hash)
- Record approval/rejection (who, previous state, new state)
- Workflow transitions
- User logins
- Record locks

`AuditService.log()` is the single creation point. Every domain service calls it.

---

## Source Lineage

Each `EmissionRecord` carries:
- `upload_session` → the file it came from
- `source_data` → JSON snapshot of normalized values at time of creation
- `version` → incremented on updates (currently v1 only, extensible)

`RawRecord` additionally holds `raw_data` (original CSV row) and `normalized_data` (post-transformation). This allows full reconstruction of the ingestion pipeline's decision for any row.

---

## Scope Categorization

| Scope | Category | Source |
|-------|----------|--------|
| Scope 1 | STATIONARY_COMBUSTION | SAP fuel invoices (diesel, gas, oil) |
| Scope 2 | PURCHASED_ELECTRICITY | Utility electricity data |
| Scope 3 | BUSINESS_TRAVEL | Corporate travel records |

Scope assignment is deterministic, set in the transformer for each source type. Scope 3 sub-categories (e.g. MOBILE_COMBUSTION for fleet fuel) can be added without schema changes.

---

## UUID Primary Keys

All models use UUID v4 PKs. Rationale:
- No sequential ID exposure (security)
- Safe to generate client-side if needed
- Merge-safe across environments
- Globally unique for audit log references

---

## Soft Deletion

`Organization` and a subset of reference data use soft deletion (`deleted_at` timestamp). `SoftDeleteManager` filters them out by default. `EmissionRecord` and `AuditLog` do not support soft deletion — they are immutable or append-only.
