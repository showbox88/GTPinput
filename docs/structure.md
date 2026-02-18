# Project Structure & Modules

## 1. Directory Layout

```text
.
├── .streamlit/
│   ├── secrets.toml      # [Sensitive] API Keys & DB Credentials
│   └── config.toml       # Streamlit Configuration
├── assets/
│   └── logo.png          # [Optional] User uploaded logo
├── modules/
│   ├── __init__.py
│   ├── auth.py           # Authentication & Session Management
│   ├── services.py       # Business Logic & Database (Supabase)
│   └── ui_v2.py          # Modern UI Components (Dashboard, Chat, Cards)
├── app.py                # Main Application Entry Point
├── expense_chat.py       # AI Chat Logic (OpenAI)
├── requirements.txt      # Project Dependencies
└── supabase_setup.sql    # Database Schema
```

## 2. Module Responsibilities

### `app.py`
The entry point. It handles:
- Page configuration (Title, Icon).
- Initializing Supabase client.
- Authentication check.
- Routing to `ui_v2.render()`.

### `modules/ui_v2.py`
The comprehensive UI library.
- **`render()`**: Main router for sub-pages.
- **`render_sidebar_nav()`**: Custom CSS-styled card navigation.
- **`render_dashboard()`**: 
    - **KPI Cards**: Total spend, trends, transaction count.
    - **Budget Cards**: Visual progress bars with health gradients.
    - **Heatmap**: Github-style activity calendar.
    - **Trend Chart**: Monthly spending bar chart.
- **`render_chat()`**: Chat interface + Settings expander (Logo upload, Logout).
- **`render_budgets()`**: Budget visuals + Management popover.
- **`render_subscriptions()`**: Recurring expense management.
- **`render_transactions()`**: Full list with filtering & editing.

### `modules/services.py`
The data layer. Encapsulates all Supabase interactions.
- **Expenses**: `load_expenses()`, `add_expense()`, `delete_expense()`.
- **Budgets**: `get_budgets()`, `add_budget()`, `update/delete_budget()`.
- **Recurring**: `get_recurring_rules()`, `add_recurring()`, `check_and_process_recurring()`.

### `modules/auth.py`
Handles user identity.
- `sign_in()`, `sign_up()`.
- `restore_session()`: Checks for existing Supabase session.

### `expense_chat.py`
Handles AI logic.
- `process_user_message()`: Sends prompts to OpenAI, parses JSON response for expense data.

## 3. Database Schema (Supabase)

### `expenses`
- `id`: UUID
- `user_id`: UUID (Foreign Key)
- `item`: Text
- `amount`: Numeric
- `category`: Text
- `date`: Date
- `note`: Text

### `budgets`
- `id`: UUID
- `user_id`: UUID
- `category`: Text
- `amount`: Numeric

### `recurring_rules`
- `id`: UUID
- `user_id`: UUID
- `name`: Text
- `amount`: Numeric
- `frequency`: Text (Monthly/Weekly/Yearly)
- `day`: Integer
- `last_triggered`: Timestamp
