# Edge Case Analysis: RupeeRadar

This document tracks potential bugs, failure modes, and corner cases across the ingestion, parsing, processing, and rendering pipelines, as well as strategies to address them.

---

## 1. File Ingestion & Parsing
- **Empty or Damaged Files**:
  - *Risk*: Pandas fails to parse, throwing unhandled tracebacks (returning 500 errors).
  - *Mitigation*: Catch parsing exceptions; validate headers and row count before processing. Return a `400 Bad Request` with message "The file uploaded is empty or invalid."
- **Password-Protected PDFs**:
  - *Risk*: File reading libraries crash or prompt for stdin.
  - *Mitigation*: Detect file type; for PDFs, attempt opening with a library and check if encrypted. Return a prompt error "This file is password-protected. Please upload a decrypted version."
- **Varying CSV/Excel Dialects (Commas, Semicolons, Encodings)**:
  - *Risk*: UTF-8 decoding failures, or treating the entire row as a single column because of semicolon delimiters.
  - *Mitigation*: Use pandas dialect sniffing or fall back to multiple common encodings (e.g. `utf-8`, `latin-1`, `cp1252`) and delimiters (`,` or `;`).
- **Header Variations**:
  - *Risk*: A bank changes "Transaction Date" to "Txn Date".
  - *Mitigation*: Implement fuzzy header mapping using lowercase regex synonyms (e.g., `date`, `txn.*date`, `value.*date`).

---

## 2. Cleaning & Normalization
- **Messy Date Formats**:
  - *Risk*: "27-06-2026", "27/06/26", and "June 27, 2026" mixed.
  - *Mitigation*: Use pandas `to_datetime(..., dayfirst=True, errors='coerce')` or custom parse formats to ensure all dates resolve to standard `YYYY-MM-DD`.
- **UPI Refund Entries**:
  - *Risk*: Refund has the word "Zomato" or "Swiggy" but is a Credit. If categorized blindly as Food, it might distort expense totals.
  - *Mitigation*: Ensure that the cleaning stage correctly assigns credit/debit types based on columns or sign. Subtract credits from category totals, or label them as positive cash flow adjustments.
- **Duplicate Entries**:
  - *Risk*: Multiple identical transactions occurring on the same day (e.g., repeating Rs.10 UPI payments for tea).
  - *Mitigation*: Include a unique transaction hash generated from `(date, amount, raw_description, balance)` instead of just date/amount to avoid treating genuine duplicates as errors, but drop exact file-upload duplicates.

---

## 3. Categorization & LLM
- **Groq API Rate Limits / Timeout**:
  - *Risk*: Ingestion hangs or returns a 500 error if Groq limits are hit.
  - *Mitigation*: Wrap Groq requests in try/except blocks. If it fails, degrade gracefully by utilizing the Rule Engine and Merchant Dictionary, classifying remaining transactions as "Other" with a warning banner.
- **Hallucinations in Structured JSON**:
  - *Risk*: LLM returns invalid JSON or nonexistent categories.
  - *Mitigation*: Enforce Pydantic schema validation or Groq JSON mode. Map unexpected categories to "Other".

---

## 4. Recurring Payment Detection
- **Variable Transaction Amounts**:
  - *Risk*: An electricity bill or utility payment recurring monthly varies from Rs.800 to Rs.1200.
  - *Mitigation*: Implement fuzzy matching on descriptions and allow a broader amount tolerance (e.g. up to $\pm 20\%$) specifically for bills and utilities.
- **Short Months (e.g. February)**:
  - *Risk*: Monthly recurring payment occurs on Jan 31st and next on Feb 28th (interval of 28 days), and then Mar 31st (interval of 31 days).
  - *Mitigation*: Set the recurrence cadence check to be flexible between 27 to 33 days.
