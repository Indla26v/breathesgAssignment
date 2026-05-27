# Breathe ESG Ingestor

Breathe ESG Ingestor is a production-grade enterprise carbon data ingestion, normalization, and review platform. It processes material consumption document logs from SAP, meter bill datasets from utility companies, and corporate travel expense files from Concur. It standardizes units of measure, performs automated anomaly screening, and enforces immutable audit locks.

---

## Architecture Summary

```
                  ┌────────────────────────────────────────┐
                  │           React Frontend (Vite)        │
                  └───────────────────┬────────────────────┘
                                      │ (HTTP APIs via Cookie JWT)
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       Django REST API Web Service      │
                  └──────┬────────────┬─────────────┬──────┘
                         │            │             │
                         │            │             │ (Enqueue Jobs)
                         ▼            ▼             ▼
       ┌───────────────────┐ ┌──────────────┐ ┌─────────────┐
       │   PostgreSQL DB   │ │ Redis Broker │ │ Celery Task │
       │ (Primary Storage) │ └──────────────┘ │   Worker    │
       └───────────────────┘                  └─────────────┘
```

- **Dual-State Records**: Retains the exact raw row payload (`RawRecord`) alongside its normalized, standardized form (`NormalizedRecord`), enabling full audit trail transparency.
- **Tenant Isolation**: Automatic multi-tenancy filters are applied via a custom model manager (`TenantAwareManager`) based on JWT context, ensuring complete partition security.
- **Precise Quantities**: Emissions calculations employ Python's `Decimal` type, avoiding floating-point rounding errors.
- **Proportional Date Splits**: Utility bills spanning month boundaries are split proportionally by day counts into distinct monthly database records.

---

## Local Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm
- Redis server (optional, SQLite is used locally for database by default)

### 1. Backend Setup

1. Navigate to the project root and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Navigate to the `backend` directory, generate migrations, and migrate the database:
   ```bash
   cd backend
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Load the sample demo fixtures (which creates a tenant, users, and enqueues files):
   ```bash
   python manage.py load_sample_data --tenant-slug=demo
   ```
4. Run the local development server:
   ```bash
   python manage.py runserver
   ```
5. In a separate terminal shell, start the Celery worker:
   ```bash
   celery -A config worker --loglevel=info
   ```

### 2. Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```
2. Start the local Vite development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173/` in your browser.

---

## Demo Login Credentials

The following credentials are created by the `load_sample_data` command:

- **Analyst Role**:
  - **Email**: `analyst@demo.com`
  - **Password**: `demo1234`
- **Tenant Admin Role**:
  - **Email**: `admin@demo.com`
  - **Password**: `demo1234`
