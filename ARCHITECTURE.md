# System Architecture

## Overview
This project is a daily expense tracking system designed for speed, decoupling, and statelessness.

## Components

### 1. User Interface (Input & Dashboard)
- **Component**: Streamlit App (`app.py`)
- **Role**: Integrated Command Center
- **Features**:
    - **Smart Chat**: Local GPT-4o integration for NLP (Record/Query/Delete).
    - **SmartDoc**: File Uploader -> GPT-4o Vision -> Archive & Expense Sync.
    - **Dashboard**: Visual Analytics & CRUD operations.

### 2. API Layer & Execution
- **Component**: Cloudflare Worker
- **Role**: Pure API Layer (REST)
- **Responsibility**:
    - CRUD operations (Add, List, Update, Delete)
    - Budget & Recurring Rules management (V3.0)
    - Authentication via `X-API-Key`

### 3. Data Storage
- **Component**: Cloudflare D1 (SQLite)
- **Tables**: `expenses`, `budgets`, `recurring_rules`

### 4. External Services
- **OpenAI**: NLP & Vision (Text parsing & Document analysis).
- **Google Workspace**: Drive/Sheets/Calendar (Archiving only).

## Data Flow (V3.0)
1. **Chat Recording**: `Streamlit` -> `OpenAI` (Parse) -> `Worker` (`/add`) -> `D1`.
2. **Chat Query**: `Streamlit` (load DF) -> `OpenAI` (Answer based on context).
3. **SmartDoc**: `Streamlit` (Upload) -> `OpenAI` (Vision) -> `Drive/Sheets` (Archive) + `Worker` (Sync Expense).
4. **Dashboard**: `Streamlit` -> `Worker` (`/list`, `/budget/list`) -> `Pandas`.

## Constraints
- Fast write path is critical.
- No dependency on Make or Google Sheets (Legacy dependencies removed).
- Database schema changes must be backward-compatible.

## Future Roadmap (Planned)
1. **Budgeting System**:
   - Set monthly limits per category.
   - Visual progress bars showing usage vs. limit.
2. **Fixed Recurring Expenses**:
   - Automated logging for regular bills (insurance, phone, subscriptions).
   - Likely requires Cloudflare Worker Triggers (Cron).
3. **Savings Plans**:
   - Goal-based savings (e.g., "Travel Fund").
   - Target amounts and periodic auto-allocation.
   - Progress visualization.
