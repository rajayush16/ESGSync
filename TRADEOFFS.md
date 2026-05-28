# ESGSync — Tradeoffs & Intentional Scope Limits

## Features Intentionally Not Implemented

### Real-Time Collaboration
**Skipped because**: WebSocket infrastructure (Django Channels + Redis pub/sub) adds significant complexity. Analysts reviewing records concurrently is an edge case for a V1. A simple "record last seen by" timestamp prevents double-approval.

### Market-Based Scope 2 Accounting
**Skipped because**: Market-based accounting (using energy attribute certificates like RECs or GOs) requires an additional data source and factor database. The location-based method (grid average) implemented here is simpler and more widely adopted for Scope 2 reporting.

### Automated GHG Factor Updates
**Skipped because**: IPCC GWP values change with each assessment report (AR5 → AR6). We use AR5 factors hardcoded in `transformer.py`. Production should version factors with effective dates and allow override.

### Email Notifications
**Skipped because**: Requires mail server configuration. Review assignment and approval notifications are high-value but out of scope for MVP. The API and data model are designed to support them without structural changes.

### Excel/XLSX Export
**Skipped because**: `openpyxl` is in requirements and the export logic is straightforward. Not implemented to keep scope focused on ingestion and review workflows.

### OAuth2 / SSO Integration
**Skipped because**: Enterprise SSO (SAML 2.0, Okta, Azure AD) integration is highly customer-specific. JWT with username/password is sufficient for MVP. The auth layer is isolated in `organizations/urls/auth.py` for easy extension.

### Scope 3 Upstream Transport & Supply Chain
**Skipped because**: Requires supplier emission factor data, activity data from procurement systems, and spend-based or hybrid calculation methods. The `EmissionCategory` enum includes these categories for future use.

### API Rate Limiting
**Skipped because**: `django-ratelimit` or DRF throttling classes can be added in one configuration change. Not implemented for MVP but the setting structure supports it.

---

## Technical Tradeoffs Accepted

### JSON source_data on EmissionRecord
Storing a JSON snapshot of normalized source data on `EmissionRecord` denormalizes the schema. The benefit is that an auditor can see exactly what data produced a given emission value without joining to `RawRecord`. The cost is that the data is duplicated and the JSON is not queryable efficiently. PostgreSQL JSONB indexes mitigate query cost.

### No Event Sourcing
The audit log is an append-only event stream but the primary entities (`EmissionRecord`, `ReviewTask`) are mutable state stores. True event sourcing would make the audit log the source of truth, with projection queries for current state. This is architecturally purer but adds significant complexity for an MVP.

### Bulk Create Without Signals
`IngestionService` uses `bulk_create` for performance. Django signals do not fire on `bulk_create`. This means any signal-based side effects (e.g., auto-creating ReviewTasks on EmissionRecord creation) must be handled explicitly in the ingestion service. This is documented and intentional.

---

## Future Improvements (Priority Order)

1. Versioned emission factors with effective dates
2. Automated ReviewTask creation on EmissionRecord status transitions
3. Scope 2 market-based accounting with REC/GO support
4. Email/Slack notification hooks on review actions
5. CSV/Excel export of approved emission records
6. SFTP/S3 automated file pickup for recurring data sources
7. Full IATA airport database for distance calculations
8. Facility-level RBAC
9. Reporting period management with fiscal year boundaries
10. Multi-approval workflow for high-value records
