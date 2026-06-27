# Implementation Plan: RupeeRadar

This document outlines the phase-by-phase roll-out schedule of RupeeRadar.

---

## Phase 1: Vertical Slice (MVP)
The goal is to establish a complete end-to-end flow using a single standard bank file format and deterministic rules.

1. **Ingestion & Basic Parsing**:
   - Create raw ingestion route `POST /api/v1/upload`.
   - Implement HDFC/SBI bank CSV parser (extract Date, Description, Debit, Credit, Balance).
2. **Basic Cleaning & Rule-Based Categorization**:
   - Normalize dates (`YYYY-MM-DD`).
   - Clean descriptions (e.g. remove transaction references, IDs).
   - Implement a simple regex rule engine mapping categories: Food (Swiggy, Zomato), Travel (Uber, Ola), Subscriptions (Netflix, Spotify), Investments (Zerodha), etc.
3. **Metrics Aggregation**:
   - Calculate basic metrics: Income, spend, savings, savings rate, and category-wise spending.
4. **Simple Dashboard Frontend**:
   - Create a clean drag-and-drop file upload UI.
   - Design a page showing total income, total spend, savings cards, a category breakdown table, and the transaction list.
5. **Template-Based Insights**:
   - Generate three fixed insights: largest debit transaction, highest spending category, and total spend.

---

## Phase 2: Intelligence & Detection
Enhance the accuracy of categories and detect repeating patterns.

1. **Groq LLM Categorization**:
   - Add integration with the Groq API.
   - For transactions not matched by rule-based categories, send a batch to Groq to classify with high confidence.
2. **Recurring Payment Detection**:
   - Group transaction descriptions using token similarities.
   - Detect groups having $\ge 2$ entries, comparable amounts ($\pm 5\%$), and interval spacings around 28-32 days.
3. **Interactive Category Override**:
   - Add dropdowns in the frontend transaction table to change categories.
   - Call `PATCH /api/v1/sessions/{id}/transactions/{txn_id}` to save the choice and trigger recalculations on the fly.
4. **Monthly Spend Trend**:
   - Add interactive line/bar chart displaying spend trends over months.

---

## Phase 3: Polish & Deliverable
Complete the features, optimize performance, handle errors, and make reports shareable.

1. **Flexible Ingestion**:
   - Add a generic column mapping dialog in the frontend if the bank statement is not automatically recognized, letting users specify which columns contain Date, Description, Amount, etc.
2. **PDF Report Export**:
   - Implement a print view optimized for saving as a high-quality PDF.
3. **Session TTL & Retention Policy**:
   - Add background worker or database check that deletes sessions after 24-72 hours.
   - Implement `DELETE /api/v1/sessions/{id}` route.
4. **LLM-Enhanced Narrative Insights**:
   - Feed aggregated metrics and category summaries to Groq to generate a narrative spending analysis.
5. **Robust Error Handling**:
   - Reject password-protected or empty statements, and return user-friendly errors.
