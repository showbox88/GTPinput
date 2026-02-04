# 💰 Expense Tracker Update - V3.0 Features

This update transforms the simple expense logger into a comprehensive personal finance tool.

## ✨ Key Features

### 1. 📅 Monthly Budget System (预算管理)
- **Automatic Tracking**: Budgets reset automatically every month.
- **Visual Progress**: Custom-designed, taller progress bars that look great in both Light and Dark modes.
- **Icon Picker**: Fun 10x4 emoji grid to personalize each category.
- **Dark Mode**: Fully optimized with translucent backgrounds and harmonious Teal accents.

### 2. 🔄 Recurring Expenses (固定开销)
- **Set & Forget**: Automatically logs bills like Rent, Netflix, or Gym memberships.
- **Flexible Rules**: Supports Weekly, Monthly, and Yearly frequencies.
- **Full Control**: Editable table to modify rules, amounts, and dates at any time.
- **Smart Integration**: Requires Cloudflare Cron Triggers for full automation, but includes a manual "Trigger" button for on-demand use.

### 3. 🎨 Visual Overhaul
- **Dark Theme**: Custom `.streamlit/config.toml` replaces the harsh default Red with a soothing **Teal (#00ADB5)**.
- **Harmonized Categories**: Standardized category lists (including "居住") across Front-end and AI Worker to ensure accurate classification.
- **Clean Console**: Eliminated all Streamlit deprecation warnings for a smoother developer experience.

## 🛠️ How to Use

1. **Add Budgets**: Go to `⚙️ Settings` -> `Budget Plans`. Pick an icon, set an amount, and save.
2. **Set Recurring**: Go to `⚙️ Settings` -> `Recurring Expenses`. Add your rent or subscriptions. 
   - *Important*: Ensure Cloudflare Trigger is set to `Daily` for automation.
3. **View Dashboard**: The homepage now shows your real-time budget burn rate alongside your spending charts.

---
*Developed with Streamlit & Cloudflare Workers*
