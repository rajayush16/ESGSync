# ESGSync — Architecture Decisions

## Why Modular Monolith?

ESG platforms have complex domain interactions: ingestion feeds normalization, normalization creates emission records, emission records trigger review tasks, reviews generate audit logs. Splitting these into microservices would require distributed transactions (saga pattern), service discovery, and inter-service authentication — all of which add latency and operational burden without proportional benefit at the scale ESG platforms operate (hundreds of thousands of records, not billions).

A modular monolith gives us:
- Single deployment unit (simpler DevOps)
- Atomic transactions across domain boundaries
- Easy refactor into services later if scale demands it
- Shared PostgreSQL with row-level isolation by organization

The Django app structure (`apps/ingestion`, `apps/normalization`, `apps/emissions`, etc.) enforces domain boundaries at the module level. Cross-app coupling is controlled — `ingestion` only imports from `normalization`; `emissions` only imports from `ingestion` for FK resolution. This boundary discipline is the key discipline of a modular monolith.

---

## Why CSV Ingestion?

1. **Realism**: SAP R/3 and S/4HANA export fuel/procurement data as CSV/Excel. Utility companies provide billing exports in CSV. Concur/Navan export travel data as CSV. This is how enterprise ESG data actually arrives.

2. **No ERP API complexity**: Connecting directly to SAP via RFC, OData, or BAPI would require SAP licenses, network VPN, and customer-specific configuration. CSV is the universal denominator.

3. **Auditability**: A CSV file is a point-in-time snapshot. It can be versioned, hashed, stored, and re-processed. API connections produce live data that is harder to audit.

4. **Incremental path**: CSV → SFTP pickup → API polling is a standard enterprise integration escalation path.

---

## Why Celery for Ingestion?

CSV files can be large (50K+ rows). Processing them synchronously in a web request would:
- Time out HTTP connections
- Block web workers
- Provide no progress visibility

Celery tasks allow:
- Async processing with status tracking (`UploadSession.status`)
- Retry on transient failures (database busy, file system errors)
- Graceful handling of large files
- Task result storage via `django-celery-results`

---

## Assumptions Made

1. **One organization per user**: Users belong to exactly one organization. Cross-org access is via admin accounts only.

2. **Emission factors are static**: GHG factors are stored as constants in `transformer.py`. In production, these should be versioned in the database with effective dates (GWP values change per IPCC report).

3. **Grid emission factors are regional averages**: We use national/regional averages (e.g. Germany: 0.385 kg CO₂e/kWh). Market-based accounting (using supplier-specific factors or renewable energy certificates) is out of scope for this MVP.

4. **Airport distance uses a representative subset**: The `AIRPORT_COORDS` dictionary covers ~60 major airports. Unknown airport codes default to `None` distance (emissions not calculated). A production deployment would use IATA's full airport database.

5. **Review tasks are created outside this MVP's automatic trigger**: The `ReviewService.create_task_for_record()` exists but is not wired to a signal in the MVP. Production would use a Django signal on `EmissionRecord` creation.

---

## Real-World Compromises

- **No RBAC at row level**: Facility managers cannot be restricted to viewing only their facility's data. Organization-level isolation is implemented; facility-level is not.
- **No approval quorum**: Records are approved by a single analyst. Enterprise deployments often require dual-approval for large emission records.
- **No export**: There is no CSV/Excel export of approved emission records. This is a common requirement.
- **No reporting period management**: Fiscal year and reporting period management is partial. Production would need quarterly/annual period definitions.

---

## Scalability Considerations

The system is designed to handle:
- ~200 concurrent users per organization
- ~1M emission records per organization per year
- CSV files up to 100MB (≈500K rows)

For larger scale:
- Celery workers can be horizontally scaled
- PostgreSQL read replicas for analytics queries
- Partition `emission_records` and `raw_records` by organization + year
- Move analytics aggregates to a materialized view or dedicated analytics DB
