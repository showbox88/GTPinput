# Changelog

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
