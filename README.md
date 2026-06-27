# RupeeRadar 🛰️

RupeeRadar is an AI-powered personal finance assistant that cleans, normalizes, and groups messy transaction descriptions (specifically optimized for Indian UPI tags, EMIs, and NEFT statements) to provide a premium CRED-like financial dashboard and professional PDF reports.

---

## 🚀 Live Demo & Deployment URLs
* **Frontend Dashboard (Vercel)**: `https://your-rupee-radar.vercel.app`
* **Backend API Gateway (Railway)**: `https://your-rupee-radar-api.up.railway.app`

---

## ✨ Features
1. **Indian Statement Ingestion**: Handles raw statement exports (CSV, Excel) from major Indian banks (HDFC, SBI, ICICI) or generic structures.
2. **Transaction Normalization**: Formats disparate date patterns, resolves debit/credit signs, and cleans transaction noise (e.g. `UPI/DR/1234567890/ZOMATO-DELHI` -> `Zomato`).
3. **Hybrid Categorization**: Employs a fast regex rule-engine paired with **Groq API Llama-3.1-8b-instant** JSON structured fallback.
4. **CRED-Inspired UX**: Beautiful glassmorphic UI, responsive tables, metallic metrics cards with mouse-tracking shine highlights, and custom cards for subscriptions.
5. **Subscription & EMI Tracker**: Grouping checks identify repeating debits that occur within 28-32 day cadences with $\pm 10\%$ amount variance.
6. **One-Click PDF Export**: Clean, print-styled stylesheet wrapper compiling all analysis, AI observations, recurring lists, and full ledger lists into a professional report.

---

## 🛠️ Technology Stack
* **Frontend**: React (v19) + TypeScript + Tailwind CSS (v3) + Vite + Recharts
* **Backend**: FastAPI + Python (v3.11+) + Pandas + SQLite
* **Database**: SQLite (Local) / SQLAlchemy ORM (support for PostgreSQL)
* **LLM Layer**: Groq Python SDK (`llama-3.1-8b-instant`)

---

## 📁 Folder Structure
```
rupee-radar/
├── docs/                      # Foundational system architecture
│   ├── problemStatement.txt   # Core challenge constraints
│   ├── context.md             # Project parameters and objectives
│   ├── architecture.md        # Technical architecture details
│   ├── implementation-plan.md # Phase details
│   └── edge-cases.md          # Edge-case error resolution checklist
├── backend/                   # FastAPI Server & Ingestion Pipelines
│   ├── app/
│   │   ├── api/
│   │   ├── models/            # SQLAlchemy schemas
│   │   ├── pipeline/          # cleaner, categorizer, recurring, metrics pipelines
│   │   └── main.py            # Entry point
│   ├── tests/
│   │   └── fixtures/          # Mock statements (CSV)
│   ├── requirements.txt
│   └── Dockerfile             # Production deployment instruction
├── frontend/                  # React Frontend Dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── App.tsx            # App core components
│   │   └── index.css          # Tailwind CSS directives & CRED effects
│   ├── tailwind.config.js
│   ├── vercel.json            # Vercel SPA routing
│   └── package.json
├── docker-compose.yml         # Container configuration
└── README.md
```

---

## ⚙️ Installation & Running

### 1. Run the Backend API
Navigate to the `backend/` directory:
```bash
# Install dependencies
pip install -r requirements.txt

# Start local server
uvicorn app.main:app --reload --port 8000
```
API runs on `http://localhost:8000`. API docs can be viewed at `http://localhost:8000/docs`.

### 2. Run the Frontend Dashboard
Navigate to the `frontend/` directory:
```bash
# Install packages
npm install

# Run Vite dev server
npm run dev
```
Web app runs on `http://localhost:3000`.

---

## 📖 API Documentation

The RESTful API is exposed under `/api/v1`:

* **`POST /api/v1/upload`**
  * *Purpose*: Uploads a bank statement.
  * *Payload*: Multipart Form-Data (file).
  * *Response*: `{ "session_id": "UUID", "status": "ready" }`

* **`GET /api/v1/sessions/{id}/transactions`**
  * *Purpose*: Returns the full list of standardized cleaned transactions.

* **`PATCH /api/v1/sessions/{id}/transactions/{txn_id}`**
  * *Purpose*: Manually overrides a transaction's category. Instantly triggers backend database recalculation for metrics and insights.
  * *Payload*: `{ "category": "Food" }`

* **`GET /api/v1/sessions/{id}/analytics`**
  * *Purpose*: Returns metrics (inflow, outflow, savings, rate), monthly trends datasets, and biggest cash flow records.

* **`GET /api/v1/sessions/{id}/insights`**
  * *Purpose*: Returns narrative AI advisor observations.

* **`GET /api/v1/sessions/{id}/recurring`**
  * *Purpose*: Returns identified subscription and EMI groups.

* **`DELETE /api/v1/sessions/{id}`**
  * *Purpose*: Purges all session data immediately for safety.
