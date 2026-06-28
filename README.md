# 🚀 RupeeRadar

> **AI-powered Personal Finance Assistant for Intelligent Bank Statement Analysis**

RupeeRadar helps users understand where their money goes by transforming messy bank statements into meaningful financial insights.

Instead of manually reviewing hundreds of UPI transactions, EMIs, subscriptions, and bank transfers, users can simply upload their bank statement and receive:

- 📊 Spending analytics
- 🏷️ Automatic expense categorization
- 🔁 Recurring payment detection
- 💰 Income vs Expense analysis
- 📈 Monthly spending trends
- 🤖 AI-generated financial insights
- 📄 Downloadable financial reports

---

# 🌟 Why RupeeRadar?

Modern banking has become digital, but understanding personal finances is still difficult.

A typical bank statement contains:

- UPI IDs
- Reference numbers
- Merchant codes
- Long transaction descriptions
- Mixed debit/credit formats

Most users cannot quickly answer questions like:

- Where did I spend most of my money?
- Which subscriptions am I paying for?
- How much did I save this month?
- Which expenses are recurring?
- What was my biggest expense?

RupeeRadar solves this problem using AI and intelligent data processing.

---

# ✨ Features

### 📂 Upload Bank Statements

- CSV Support
- Excel Support
- Generic bank statement parsing
- Optimized for Indian banking formats

---

### 🧹 Transaction Cleaning

Automatically converts messy transaction descriptions into readable merchant names.

Example

```
UPI/DR/9876543210/ZOMATO-DELHI
```

↓

```
Zomato
```

---

### 🤖 AI-powered Categorization

Hybrid categorization engine using:

- Rule-based engine
- Merchant dictionary
- Groq Llama 3.1 fallback

Categories include:

- Food
- Shopping
- Travel
- Bills
- Salary
- Investments
- EMI
- Rent
- Subscriptions
- Others

---

### 🔁 Recurring Payment Detection

Automatically detects:

- Netflix
- Spotify
- EMIs
- SIPs
- Insurance
- Rent
- Electricity bills

using frequency and amount similarity.

---

### 📊 Financial Dashboard

Interactive dashboard includes:

- Total Income
- Total Expenses
- Savings
- Savings Rate
- Top Spending Categories
- Monthly Trends
- Largest Transactions

---

### 📈 Spending Analytics

Visual reports with:

- Pie Charts
- Bar Charts
- Monthly Trends
- Category Distribution

---

### 📄 PDF Report Export

Generate a clean financial report including:

- Summary
- Charts
- Insights
- Recurring Payments
- Transaction History

---

# 🏗️ System Architecture

```
                Bank Statement
                     │
                     ▼
         CSV / Excel Upload
                     │
                     ▼
          Transaction Parsing
                     │
                     ▼
      Cleaning & Normalization
                     │
                     ▼
     AI Expense Categorization
                     │
                     ▼
    Recurring Payment Detection
                     │
                     ▼
 Financial Metrics & Analytics
                     │
                     ▼
       Dashboard + PDF Report
```

---

# 🛠️ Tech Stack

## Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
- Recharts

## Backend

- FastAPI
- Python 3.11
- Pandas
- SQLAlchemy

## Database

- SQLite
- PostgreSQL Ready

## AI

- Groq API
- Llama 3.1 8B Instant

---

# 📂 Project Structure

```
rupee-radar/

├── backend/
│   ├── app/
│   ├── models/
│   ├── pipeline/
│   ├── api/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── assets/
│   └── App.tsx
│
├── docs/
│   ├── architecture.md
│   ├── context.md
│   ├── implementation-plan.md
│   ├── edge-cases.md
│   └── problemStatement.md
│
├── screenshots/
│
├── docker-compose.yml
│
└── README.md
```

---

# 📸 Screenshots

## Dashboard

> Add screenshot here

```
screenshots/dashboard.png
```

---

## Analytics

> Add screenshot here

```
screenshots/analytics.png
```

---

## AI Insights

> Add screenshot here

```
screenshots/insights.png
```

---

## Upload Page

> Add screenshot here

```
screenshots/upload.png
```

---

# ⚙️ Local Installation

## Clone Repository

```bash
git clone https://github.com/gaurav-product/rupee-radar.git

cd rupee-radar
```

---

## Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend:

```
http://localhost:8000
```

Swagger Documentation:

```
http://localhost:8000/docs
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```
http://localhost:5173
```

---

# 🔌 API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/upload` | Upload bank statement |
| GET | `/api/v1/sessions/{id}/transactions` | View cleaned transactions |
| PATCH | `/api/v1/sessions/{id}/transactions/{txn_id}` | Update category |
| GET | `/api/v1/sessions/{id}/analytics` | Financial analytics |
| GET | `/api/v1/sessions/{id}/insights` | AI insights |
| GET | `/api/v1/sessions/{id}/recurring` | Recurring payments |
| DELETE | `/api/v1/sessions/{id}` | Delete session |

---

# 🤖 AI Workflow

RupeeRadar follows a hybrid AI pipeline.

```
Transaction

↓

Rule Engine

↓

Merchant Dictionary

↓

Groq AI

↓

Category Prediction

↓

Financial Insights
```

This approach minimizes AI calls while maintaining accurate categorization.

---

# 🔒 Privacy

Financial information is sensitive.

RupeeRadar is designed with privacy in mind:

- No permanent storage of uploaded statements
- Session-based processing
- Minimal data shared with AI services
- Support for automatic session deletion

---

# 🚀 Future Roadmap

- PDF Statement Parsing
- OCR Support
- Budget Planner
- Spending Forecasting
- Personalized AI Financial Advisor
- Investment Insights
- Mobile Application
- Multi-language Support

---

# 👨‍💻 Author

**Gaurav Kumar Singh**

Aspiring Product Manager | AI Builder | Healthcare & Wellness Innovator

GitHub

https://github.com/gaurav-product

LinkedIn

(Add your LinkedIn profile here)

---

# ⭐ Support

If you found this project interesting:

⭐ Star this repository

🍴 Fork it

💡 Share your feedback

---

# 📄 License

This project is licensed under the MIT License.

---

## 🎯 Built For

This project was built as part of an AI Engineering Challenge focused on solving real-world financial problems using Artificial Intelligence, FastAPI, React, and Large Language Models.
