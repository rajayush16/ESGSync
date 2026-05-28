# ESGSync

**Enterprise ESG Data Ingestion & Review Platform**

ESGSync is a production-grade platform for ingesting, normalizing, validating, and reviewing sustainability and emissions data from enterprise source systems. It supports the full lifecycle from raw CSV export to auditor-locked emission records.

---

## Architecture Overview

```
ESGSync
├── backend/                  Django + DRF + Celery
│   ├── apps/
│   │   ├── organizations/   Multi-tenancy, users, roles
│   │   ├── ingestion/       Upload sessions, parsers, validation
│   │   ├── normalization/   Unit conversion, schema mapping, transformers
│   │   ├── emissions/       Emission records, scope categorization
│   │   ├── reviews/         Analyst review workflow
│   │   ├── audit/           Immutable audit trail
│   │   ├── analytics/       Dashboard metrics and aggregates
│   │   └── common/          Base models, enums, exceptions, middleware
│   └── config/              Settings, URLs, Celery config
├── frontend/                 React + TypeScript + Tailwind + TanStack Query
│   └── src/
│       ├── pages/           8 application pages
│       ├── components/      Shared UI components
│       ├── services/        Typed API service layer
│       ├── types/           Full TypeScript type definitions
│       └── utils/           Formatters, color helpers
├── sample_data/              Realistic test CSVs with edge cases
├── MODEL.md                  Data model and design decisions
├── DECISIONS.md              Architecture rationale
├── TRADEOFFS.md              Scope boundaries and future work
└── SOURCES.md                Research basis for emission factors
```

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### With Docker Compose

```bash
# Clone and start all services
docker compose up -d

# Run migrations and create a superuser
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser

# Load sample data sources (optional)
docker compose exec backend python manage.py shell -c "
from apps.organizations.models import Organization
from apps.ingestion.models import DataSource
from apps.common.enums import DataSourceType

# Create a demo org and data sources
org = Organization.objects.create(name='Acme Corporation', slug='acme', industry_sector='Manufacturing', country='DE')
DataSource.objects.create(organization=org, name='SAP Fuel Procurement', source_type=DataSourceType.SAP_FUEL)
DataSource.objects.create(organization=org, name='Utility Electricity', source_type=DataSourceType.UTILITY_ELECTRICITY)
DataSource.objects.create(organization=org, name='Corporate Travel', source_type=DataSourceType.CORPORATE_TRAVEL)
"
```

Access:
- Frontend: http://localhost:5173
- API: http://localhost:8000/api/v1/
- API Docs: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements/local.txt
cp .env.example .env          # Edit with your DB/Redis credentials
python manage.py migrate
python manage.py runserver
# In another terminal:
celery -A config worker -l info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Data Sources

Upload sample CSV files from `sample_data/` to test the full pipeline:

| File | Source Type | Notable Edge Cases |
|------|-------------|-------------------|
| `sap_fuel_procurement.csv` | SAP_FUEL | German date formats, missing vendor, negative quantity, duplicate invoice, unrecognized unit |
| `utility_electricity.csv` | UTILITY_ELECTRICITY | Mixed date formats, zero usage, electricity spike (3.3×), invalid period order, missing kWh |
| `corporate_travel.csv` | CORPORATE_TRAVEL | Same origin/destination, excessive hotel nights (45), transposed fields |

---

## API Reference

All endpoints require JWT authentication (`Authorization: Bearer <token>`).

```
POST   /api/v1/auth/token/              Login
POST   /api/v1/auth/token/refresh/      Refresh token
GET    /api/v1/auth/me/                 Current user

POST   /api/v1/uploads/sessions/upload/ Upload CSV file
GET    /api/v1/uploads/sessions/        List upload history
GET    /api/v1/uploads/sessions/{id}/   Session detail
GET    /api/v1/uploads/sessions/{id}/records/  Row-level records

GET    /api/v1/emissions/               List emission records
GET    /api/v1/emissions/summary/       Totals by scope
POST   /api/v1/emissions/{id}/approve/  Approve record
POST   /api/v1/emissions/{id}/reject/   Reject record (reason required)
POST   /api/v1/emissions/{id}/lock-for-audit/

GET    /api/v1/reviews/                 Review queue
POST   /api/v1/reviews/{id}/approve/    Analyst approve
POST   /api/v1/reviews/{id}/reject/     Analyst reject
POST   /api/v1/reviews/{id}/assign/     Assign to analyst

GET    /api/v1/audit/                   Audit log (immutable)
GET    /api/v1/audit/entity/{type}/{id}/ Entity history

GET    /api/v1/analytics/overview/      Dashboard KPIs
GET    /api/v1/analytics/emissions-by-month/
```

---

## Testing

```bash
cd backend
pytest apps/normalization/tests/
pytest apps/ingestion/tests/
pytest apps/audit/tests/

# Full suite
pytest --cov=apps --cov-report=term-missing
```

---

## User Roles

| Role | Capabilities |
|------|-------------|
| ADMIN | Full access, user management, organization settings |
| DATA_MANAGER | Upload files, manage data sources, reprocess uploads |
| ANALYST | Review and approve/reject emission records |
| AUDITOR | Lock records for audit, view full audit trail |
| VIEWER | Read-only access to emissions and reports |

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | JWT authentication |
| Dashboard | `/dashboard` | KPI overview, scope breakdown, recent uploads |
| Upload Center | `/uploads` | File upload with drag-and-drop |
| Upload History | `/uploads/history` | All sessions with status and success rate |
| Session Detail | `/uploads/:id` | Row-level records, validation errors, anomalies |
| Review Queue | `/reviews` | Analyst approval/rejection workflow |
| Suspicious Records | `/suspicious` | Anomaly-flagged rows across all uploads |
| Emissions Explorer | `/emissions` | Filterable emission records table |
| Record Details | `/emissions/:id` | Full record detail with audit history |
| Audit Timeline | `/audit` | Immutable event log with action filters |

---

## Engineering Principles

- **No over-engineering**: Every abstraction has a concrete purpose
- **Auditability first**: Every state change is logged immutably
- **Domain-driven modules**: Cross-app imports follow strict dependency direction
- **Realistic data modeling**: Emission factors, unit conversions, and anomaly rules are research-backed
- **Type safety**: Strict TypeScript throughout frontend; Django model typing via type hints
- **Testable boundaries**: Parsers, validators, and transformers are unit-testable without a database

---

## Documentation

- [MODEL.md](MODEL.md) — Data model, multi-tenancy, normalization strategy
- [DECISIONS.md](DECISIONS.md) — Architecture decisions and rationale
- [TRADEOFFS.md](TRADEOFFS.md) — Intentional scope limits and future work
- [SOURCES.md](SOURCES.md) — Research basis for emission factors and data formats
