# LankaMart – Business Process Support (Unit 17)

Synthetic e-commerce decision-support prototype: **React + TypeScript** dashboard, **FastAPI** backend, **SQL database (SQLite via SQLAlchemy)**, **scikit-learn Random Forest** late-delivery model.

## Run
### 1. Backend (Python 3.10+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_and_train.py          # creates lankamart.db (1,200 orders), trains model, writes powerbi_orders.csv + metrics.json
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### 2. Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173 (proxies /api to :8000)
```

## Database
Table `orders` (see `backend/app/models.py`). Set `DATABASE_URL` to use another SQL DB (e.g. PostgreSQL) – note the monthly query uses `substr` on ISO dates (SQLite/Postgres-text style); adjust for other engines.

## Endpoints
`/api/health`, `/api/summary`, `/api/monthly-sales`, `/api/category-sales`, `/api/region-sales`, `/api/recent-orders`, `/api/model-metrics`, `POST /api/predict-late-delivery`

## Power BI
Import `backend/powerbi_orders.csv` (or connect Power BI to the SQLite DB via ODBC). Build cards, line/bar charts and slicers; save the .pbix yourself.

## Before submission (do these yourself)
Run everything, capture real screenshots, fill the test table with ACTUAL results, build the .pbix. Metrics come from synthetic data – do not present them as real-world performance.
