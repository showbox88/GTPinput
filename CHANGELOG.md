# Changelog

## [V3.7] - 2026-02-21
### Full Localization & UI Purification
- **100% i18n Coverage**: Implemented a comprehensive translation system (JSON-based) covering all UI labels, form fields, buttons, and AI assistant responses.
- **CSS-Injected Translation**: Bypassed Streamlit's hardcoded limitations to localize the File Uploader component ("Drag and drop", "Browse files").
- **Minimalist Chart UI**: Purified chart visuals by removing redundant axis titles ("Amount", "Date") and cleaning up hover popup information globally.
- **Sidebar UX Refinement**: Restructured the sidebar to remove redundant titles and localized the AI Smart Assistant header.
- **Form & Validation i18n**: Fully localized error messages, success banners, and selection frequencies (Monthly, Weekly, Yearly) in all management views.

## [V3.6] - 2026-02-20
### Global Multi-Currency Support & AI Optimization
- **Dynamic Currency Selector**: Users can now select their preferred currency (e.g., USD, CNY, EUR, THB) from the Settings page. This preference is permanently stored in Supabase `user_metadata`.
- **AI Exchange Rate Engine**: Re-engineered the `SYSTEM_PROMPT` in `expense_chat.py` to enforce the user's primary currency in all money-related replies, whilst granting the AI explicit permission to calculate real-time exchange rate estimates when cross-currency queries are asked.
- **UI Currency Injection**: All Dashboard KPI cards, Heatmaps, Budget progress bars, and data tables now dynamically render the user's selected symbol instead of hardcoded USD/CNY.

## ARCHITECTURE
- **`modules/`**: Contains all reusable logic and UI components.
    - `auth.py`: Handles login/signup/session.
    - `services.py`: Handles all database interactions.
    - `ui_v2.py`: Handles all rendering and frontend styling, including CSS-based component overrides.
    - `i18n.py`: **[NEW]** Centralized translation engine for multi-language support.
- **`locales/`**: **[NEW]** JSON dictionaries for internationalization (`zh.json`, `en.json`).
- **`app.py`**: Minimalist entry point, acting as a router.

## [V3.5] - 2026-02-19
### Professional UI & Robust Rendering
- **Unified KPI Card V3**: Aesthetic redesign featuring glassmorphism, bold hero typography, and text gradients for a professional financial look.
- **Improved HTML Rendering**: Fixed a critical bug where indentation in HTML strings caused Streamlit to render raw code blocks instead of the intended UI.
- **Adaptive Spacing**: Optimized vertical padding on mobile budget cards to improve visual hierarchy and readability.
- **Structural Separation**: Isolated mobile and desktop budget card rendering logic to ensure cross-platform stability.

## [V3.4] - 2026-02-19
### Mobile UI Polish
- **Unified Mobile Dashboard**: Consolidated KPI card, optimized layout for small screens.
- **Floating Navigation**: Persistent, transparent bottom bar with glassmorphism effect for quick access to Dashboard/Chat.
- **Compact Components**: Ultra-compact budget progress bars (12px), responsive heatmap adjustments to prevent overlap.
- **Visual Enhancements**: Professional dark blue gradient for navigation buttons, cleaner charts (removed axis labels), larger pie chart.
- **UX Improvements**: Auto-focus chat input on mobile, overlap prevention for better readability.

## [V3.3] - 2026-02-19
### Visual Overhaul
- **Budget Cards Redesign**: Dual-color cards with professional dark blue header, thick progress bars (40px) with color warnings, and "Today" timeline indicator.
- **Daily Advice**: Automatic calculation of recommended daily spending based on remaining budget.
- **Visual Consistency**: Unified KPI title styles and strictly aligned Heatmap height.

## [V3.2] - 2026-02-10
### Added
- **Responsive Layout**: Updated `app.py` to use `layout="wide"`, improving usability on desktop and mobile.
- **Weekly Recurring Expenses**: Added logic to support `frequency="Weekly"` in both `app.py` and `scripts/cron_job.py`.
- **Date Picker UI**: Replaced integer input with `st.date_input` for recurring expense start dates.
- **Explicit Delete**: Added "Delete" checkbox columns to Budget and Recurring Expense data editors for easier management.

### Fixed
- **Recurring Logic**: Fixed logic to correctly identify "Day of Month" vs "Day of Week".
- **Syntax Errors**: Fixed `pd.Timestamp` mixed argument errors.
- **Legacy Code**: Removed redundant code blocks in `app.py`.

## [V3.1]
### Added
- **Persistent Login**: Added "Remember Me" functionality using local `.session_cache`.
- **Manual Refresh**: Added sidebar refresh button.
- **UI Improvements**: Added "Thinking..." animation and improved sort order.

## [V3.0]
### Added
- **Monthly Budgets**: Budget management with visual progress bars.
- **Recurring Expenses**: Automated cron-based expense recording.
- **New UI**: Deep Blue theme and new dashboard layout.
