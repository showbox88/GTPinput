# Implementation Plan - Budget & Recurring System (V3.0)

This plan outlines the addition of two major features: **Monthly Budgets** and **Recurring Expenses** (Fixed Costs).

## User Review Required

> [!IMPORTANT]
> **Cloudflare Cron Trigger**: For "Recurring Expenses" to run automatically, you MUST configure a **Cron Trigger** in Cloudflare Dashboard.
> 1. Go to your Worker -> **Triggers**.
> 2. Click **Add Cron Trigger**.
> 3. Set standard schedule (e.g., `0 0 * * *` for daily check at midnight UTC).
>
> **Database Migration**: Two new tables (`budgets`, `recurring_rules`) are required.

## Proposed Changes

### 1. Database (Cloudflare D1)

#### Table: `budgets`
Stores monthly spending limits.
```sql
CREATE TABLE budgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,          -- "Food Plan"
  category TEXT NOT NULL,      -- "Dining"
  amount REAL NOT NULL,        -- 3000
  color TEXT DEFAULT '#FF4B4B',
  icon TEXT DEFAULT '💰',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### Table: `recurring_rules`
Stores rules for automatic recording.
```sql
CREATE TABLE recurring_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,          -- "Rent"
  amount REAL NOT NULL,        -- 2000
  category TEXT NOT NULL,      -- "Housing"
  frequency TEXT NOT NULL,     -- 'weekly', 'monthly', 'yearly'
  day INTEGER NOT NULL,        -- 1-7 (Mon-Sun), 1-31 (Day of Month), or DayOfYear
  last_run_date TEXT,          -- "2023-10-01"
  active BOOLEAN DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Backend (Cloudflare Worker)

Modify `worker/index.js` to handle both features.

#### [NEW] Budget Endpoints
- `POST /budget/add`, `POST /budget/delete`, `GET /budget/list`

#### [NEW] Recurring Expense Endpoints
- `POST /recurring/add`: Define a rule (e.g., "Monthly on 1st").
- `POST /recurring/delete`: Remove a rule.
- `GET /recurring/list`: View active rules.
- `GET /recurring/check`: (Optional) Manual trigger to check and run pending rules.

#### [NEW] Scheduled Event Handler
Implement the `scheduled` event listener in the Worker.
- **Logic**:
    1.  Wake up on Cron Trigger (e.g., Daily).
    2.  Scan `recurring_rules`.
    3.  If `today` matches rule condition AND `last_run_date` != today:
        - Insert record into `expenses` table.
        - Update `last_run_date`.

### 3. Frontend (Streamlit)

Refactor UI to accommodate new "Settings / Management" area.

#### Sidebar / Settings Tab
- **Budget Manager**: Add/List/Delete budgets.
- **Recurring Manager**:
    - Form: Name, Amount, Category.
    - Frequency Selector: Weekly (Mon-Sun), Monthly (Day 1-31), Yearly.
    - List: Show active rules with "Delete" icon.

#### Dashboard Improvements
- **Budget Overview**: Visual Progress Bars (Actual vs Limit).
- **Auto-Refresh**: Ensuring recurring expenses appear in the list once processed.

## Verification Plan

### Budget Verification
1.  Create Budget: "Food", $500.
2.  Add Expense: "Lunch", $100.
3.  Check Progress: Should be 20%.

### Recurring Verification
1.  Create Rule: "Test Subscription", $10, Daily (for testing) or "Weekly" on Today's weekday.
2.  **Trigger**: Since we can't wait for Cron, we will use the `GET /recurring/check` endpoint or Cloudflare's "Test Scheduled Event" button.
3.  Check: Verify record appears in `expenses` and `last_run_date` updates.
