# Project Context: RupeeRadar

RupeeRadar is an AI-powered personal finance assistant that helps users understand where their money is going by analyzing their bank statement data. 

## Background
Working professionals execute hundreds of monthly transactions across UPI, credit/debit cards, bank transfers, EMIs, rent, shopping, food delivery, travel, and investments. While bank statements hold all this information, they are notoriously difficult to digest because:
- Transaction descriptions are messy, inconsistent, and often filled with cryptic codes (e.g., merchant IDs, UPI transaction reference numbers).
- Manual categorization is slow, error-prone, and unsustainable for users.
- Traditional tools fail to capture recurring expenses or provide narrative insights.

## Objective
Create an end-to-end web application that takes raw statement files, parses and cleanses them, runs an intelligence pipeline to categorize and detect patterns, and presents the insights in an intuitive dashboard.

### Key Questions Addressed
- What are my biggest spending categories?
- How much did I spend this month?
- Which transactions are recurring subscriptions or EMIs?
- What was my biggest transaction?
- What are the top insights from my spending behavior?

## Core Requirements
1. **Ingestion & Support**: Accept bank statement data (specifically CSV/Excel formats) via drag-and-drop or select file interface.
2. **Standardization**: Clean and normalize transaction fields (ISO 8601 dates, standard amounts, merchant/recipient extraction).
3. **Categorization**: Classify expenses into standard groups: `Food`, `Travel`, `Shopping`, `Bills`, `EMI`, `Subscriptions`, `Salary`, `Rent`, `Investments`, and `Other`.
4. **Recurring Detection**: Identify recurring outflows (subscriptions, EMIs, rent, SIPs, insurance) using heuristics.
5. **Key Financial Metrics**: Compute total income, total spend, savings, savings rate, biggest transaction, etc.
6. **Narrative Insights**: Generate at least 3 personalized, human-readable insights (templated & LLM-enhanced).
7. **User Interface**: Present results in a responsive, clean dashboard with interactive components (filters, category override, monthly trend charts, export to PDF/print).
