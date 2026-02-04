# System Architecture

## Overview
This project is a daily expense tracking system designed for speed, decoupling, and statelessness.

## Components

### 1. User Interface (Input)
- **Component**: Custom GPT
- **Role**: Daily Expense Recording Assistant
- **Responsibility**:
    - Natural language processing
    - Extracts `amount`, `category`, `description`, `date`
    - Calls `addExpense` tool
- **Constraint**: Stateless

### 2. API Layer & Execution
- **Component**: Cloudflare Worker
- **Role**: Pure API Layer
- **Responsibility**:
    - CRUD operations
    - No UI or AI logic
- **Endpoints** (Typical):
    - `POST /expense`
    - `GET /expenses` (Note: Current implementation uses `/list`)
    - `PUT /expense/:id`
    - `DELETE /expense/:id`
    - `GET /stats`

### 3. Data Storage
- **Component**: SQLite (via Cloudflare D1 or similar)
- **Schema**: `expenses` table
    - `id`
    - `amount`
    - `category`
    - `description`
    - `date`
    - `created_at`
- **Design**: Flat schema, no nested JSON.

### 4. Visualization (Frontend)
- **Component**: Streamlit App
- **Role**: Read-only Dashboard
- **Responsibility**:
    - Fetch data from API (No direct DB access)
    - Visualization (Trends, Pie Charts)
    - List view
- **Current Implementation**: `app.py`

## Data Flow
User -> GPT -> (tool call) -> Cloudflare Worker -> SQLite -> Streamlit

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
