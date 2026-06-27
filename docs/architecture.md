# System Architecture: RupeeRadar

This document outlines the design, layers, data models, APIs, and pipelines of **RupeeRadar**.

---

## 1. Architectural Goals
- **End-to-End Workflow**: Seamless user journey from bank statement upload to interactive dashboard and exportable report.
- **Messy-Data Tolerance**: Resilient parser & normalization pipeline specifically tailored for Indian UPI/bank descriptions.
- **Privacy by Design**: Session-scoped data, no persistent long-term storage of sensitive transaction rows beyond configurable TTL, and minimal data shared with third-party LLMs (anonymized/batch transaction details only).
- **Extensible Parsing**: Modular parser design allowing new bank templates to plug in without modifying the core pipeline.
- **Inspectable Output**: Transparency for the user—showing cleaned names alongside raw descriptions, and allowing category overrides.

---

## 2. Technology Stack (Prototype)
- **Frontend**: Vite + React + TypeScript + Vanilla CSS
  - State Management: React Context / Local State + React Query / SWR
  - Charting: Recharts or Chart.js
- **Backend**: Python FastAPI
  - Data Processing: pandas
  - Database: SQLite (local)
  - LLM Integration: Groq API client
- **Deployment**: Docker Compose for local validation

---

## 3. Core Domain Model

### 3.1 UploadSession
- `id` (UUID)
- `filename` (string)
- `file_type` (string)
- `status` (`pending` | `parsing` | `processing` | `ready` | `failed`)
- `uploaded_at` (datetime)
- `expires_at` (datetime)
- `error_message` (optional string)

### 3.2 Transaction
- `id` (string/UUID)
- `session_id` (UUID)
- `date` (ISO 8601 string: `YYYY-MM-DD`)
- `description_raw` (string)
- `description_clean` (string)
- `amount` (float, negative for debits, positive for credits)
- `type` (`credit` | `debit`)
- `balance` (optional float)
- `category` (string, matching taxonomy)
- `category_confidence` (float: 0.0 - 1.0)
- `is_recurring` (boolean)
- `recurring_group_id` (optional UUID)
- `metadata` (JSON: UPI ref, mode, parser hints)

### 3.3 RecurringGroup
- `id` (UUID)
- `session_id` (UUID)
- `label` (string, e.g., "Netflix", "Home Loan EMI")
- `category` (string)
- `frequency` (`weekly` | `monthly` | `quarterly` | `yearly` | `unknown`)
- `typical_amount` (float)
- `last_seen_date` (ISO 8601 string)
- `transaction_ids` (array of strings)
- `confidence` (float)

### 3.4 AnalysisResult
- `session_id` (UUID)
- `metrics` (JSON: income, spend, savings, savings rate, etc.)
- `top_categories` (array of objects)
- `biggest_transactions` (array of transactions)
- `insights` (array of strings)
- `generated_at` (datetime)

---

## 4. Processing Pipeline

The ingestion pipeline handles raw file execution sequentially:
1. **Upload & Store**: Accepts CSV file. Generates `session_id`.
2. **Parse & Extract**: Modular parsers select headers and load rows into standard raw structures.
3. **Clean & Normalize**: Normalizes dates to `YYYY-MM-DD`, strips UPI noise (e.g. `UPI/DR/123456/SWIGGY` -> `SWIGGY`), resolves debit/credit signs.
4. **Categorize**:
   - Level 1: Hardcoded regex/rules.
   - Level 2: Exact matching against known merchant database.
   - Level 3: Groq LLM fallback for unrecognized descriptions.
5. **Recurring Detection**: Filters debits, groups by description similarity (token matching/fuzzy match), checks for $\ge 2$ occurrences within 28-32 day intervals.
6. **Metrics & Aggregations**: Sums debits, credits, savings rate.
7. **Insights Generation**: Triggers template rules (e.g. largest spend, recurring total) + Groq narrative summary.

---

## 5. API Endpoints

- `POST /api/v1/upload` - Upload file, returns `session_id` and initial processing status.
- `GET /api/v1/sessions/{id}` - Returns session processing status.
- `GET /api/v1/sessions/{id}/transactions` - Paginated/filtered transaction list.
- `PATCH /api/v1/sessions/{id}/transactions/{txn_id}` - Overrides the category of a transaction.
- `GET /api/v1/sessions/{id}/recurring` - Returns detected recurring groups.
- `GET /api/v1/sessions/{id}/analytics` - Returns summary metrics, category totals, and trend datasets.
- `GET /api/v1/sessions/{id}/insights` - Returns generated text insights.
- `GET /api/v1/sessions/{id}/report` - Returns print/download report formatting details.
- `DELETE /api/v1/sessions/{id}` - Deletes all session records for security/privacy.
