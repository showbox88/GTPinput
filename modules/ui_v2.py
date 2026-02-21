import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import datetime
import pytz
import modules.services as services
import modules.utils as utils
import streamlit.components.v1 as components

# Optional imports
try:
    import expense_chat
except ImportError:
    pass

CATEGORIES = ["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "居住", "其他"]

# ==========================================
# CUSTOM CSS & COMPONENTS
# ==========================================
# UI Version: 2.1 (Force Update - Alignment Fixes)
def inject_custom_css():
    st.markdown("""
    <style>
        /* Global Font & Background */
        /* Removed Google Fonts to improve loading speed in China */
        
        .stApp {
            background-color: #000000;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
        }

        div.block-container {
            padding-top: 6rem;
            padding-bottom: 2rem;
        }

        /* Card Container */
        .card-container {
            background-color: #121212;
            border: 1px solid #2A2A2A;
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 12px;
        }

        /* Global KPI Title Style (Used in Heatmap, Trend, Recent) */
        .kpi-title {
            font-size: 1.15rem;
            opacity: 0.95;
            font-weight: 700; /* Bold */
            margin-bottom: 4px;
            color: #eee;
        }

        /* KPI Visual Card */
        .kpi-card-visual {
            border-radius: 16px;
            padding: 20px;
            color: white;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .kpi-card-visual .kpi-title { margin-bottom: 4px; } /* Ensure margin logic stays */
        .kpi-card-visual .kpi-value { font-size: 1.8rem; font-weight: 800; margin: 4px 0; font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
        .kpi-card-visual .kpi-meta { font-size: 0.8rem; opacity: 0.6; margin-top: 4px; }
        
        .kpi-blue { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); }
        .kpi-purple { background: linear-gradient(135deg, #23074d 0%, #cc5333 100%); } 
        .kpi-dark { background: linear-gradient(to right, #232526, #414345); }

        /* Ghost Button Strategy (Negative Margin Overlay) */
        
        /* 1. Target the button wrapper inside columns that have our KPI cards */
        /* Support both legacy 'column' and new 'stColumn' test-ids */
        div[data-testid*="olumn"]:has(#kpi-card-1) .stButton,
        div[data-testid*="olumn"]:has(#kpi-card-2) .stButton,
        div[data-testid*="olumn"]:has(#kpi-card-3) .stButton {
            width: 100% !important;
            margin-top: -140px !important; /* Pull button up over the card */
            position: relative !important;
            z-index: 10 !important;
            opacity: 0 !important; /* Make invisible */
            pointer-events: auto !important;
        }

        /* 2. Target the button element itself to fill the wrapper */
        div[data-testid*="olumn"]:has(#kpi-card-1) .stButton button,
        div[data-testid*="olumn"]:has(#kpi-card-2) .stButton button,
        div[data-testid*="olumn"]:has(#kpi-card-3) .stButton button {
            width: 100% !important;
            height: 140px !important;
            border: none !important;
        }

        /* 3. Ensure the Card is below the button in stacking context but visible */
        #kpi-card-1, #kpi-card-2, #kpi-card-3 {
            position: relative;
            z-index: 1;
            height: 140px; /* Fixed height to match button */
            pointer-events: none; /* Let clicks pass through if needed, though button is on top */
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #000000;
            border-right: 1px solid #2A2A2A;
        }

        /* Heatmap Grid */
        .heatmap-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(10px, 1fr));
            gap: 4px;
            margin-top: 10px;
        }
        .heatmap-cell {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
        
        /* Unified Card Style for st.container(border=True) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #121212 !important;
            border: 1px solid #2A2A2A !important;
            border-radius: 16px;
            padding: 20px;
        }
        /* Hide Streamlit default UI elements (Manage App, Footer, etc) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stAppDeployButton {display:none;}
        [data-testid="stToolbar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

def render_sidebar_nav():
    st.markdown("""
    <style>
        div[data-testid="stRadio"] > label { display: none; }
        div[data-testid="stRadio"] div[role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        div[data-testid="stRadio"] label {
            background: transparent;
            border: 1px solid transparent; 
            border-radius: 8px;
            padding: 10px 15px;
            text-align: left;
            transition: all 0.2s;
        }
        div[data-testid="stRadio"] label:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.1);
        }
        div[data-testid="stRadio"] label[data-checked="true"] {
            background: rgba(46, 134, 193, 0.1) !important;
            border-left: 4px solid #56CCF2 !important;
            color: #56CCF2 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
# Helper for Navigation Options
NAV_OPTIONS = {
    "Dashboard": "📊  概览 (Dashboard)",
    "Smart Chat": "💬  助手 (AI Chat)",
    "Settings": "⚙️  账号与设置 (Settings)"
}

def render_sidebar_nav():
    st.markdown("""
    <style>
        div[data-testid="stRadio"] > label { display: none; }
        div[data-testid="stRadio"] div[role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px 15px;
            text-align: left;
            transition: all 0.2s;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            width: 100%; /* Force full width */
            display: block; /* Ensure block layout */
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            background: rgba(46, 134, 193, 0.1);
            border-color: rgba(46, 134, 193, 0.3);
            transform: translateY(-2px);
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
            background: linear-gradient(135deg, rgba(46, 134, 193, 0.2) 0%, rgba(86, 204, 242, 0.1) 100%) !important;
            border: 1px solid #56CCF2 !important;
            color: #56CCF2 !important;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(86, 204, 242, 0.2);
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label p {
            font-size: 1.1rem !important;
        }
        /* Hide the radio circle */
        div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Reverse map for value lookup
    rev_options = {v: k for k, v in NAV_OPTIONS.items()}
    
    # Ensure session state exists
    if "v2_page" not in st.session_state:
        st.session_state["v2_page"] = "Dashboard"
        
    # Determine current index
    current_page = st.session_state["v2_page"]
    current_label = NAV_OPTIONS.get(current_page)
    
    idx = None
    if current_label:
        try:
            idx = list(NAV_OPTIONS.values()).index(current_label)
        except ValueError:
            idx = None

    def on_nav_change():
        sel = st.session_state["v2_nav_radio"]
        if sel in rev_options:
            st.session_state["v2_page"] = rev_options[sel]
    
    
    st.radio(
        "Menu",
        list(NAV_OPTIONS.values()),
        index=idx,
        label_visibility="collapsed",
        key="v2_nav_radio",
        on_change=on_nav_change
    )

    return st.session_state["v2_page"]

def render_mobile_bottom_nav():
    st.markdown("""
    <style>
        .mobile-nav-container {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #121212;
            border-top: 1px solid #333;
            z-index: 9999;
            display: flex;
            justify-content: space-around;
            padding: 10px 0;
            padding-bottom: max(10px, env(safe-area-inset-bottom));
        }
        .mobile-nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            color: #888;
            font-size: 0.75rem;
            text-decoration: none;
            background: none;
            border: none;
            cursor: pointer;
            width: 25%;
        }
        .mobile-nav-item.active {
            color: #56CCF2;
        }
        .mobile-nav-icon {
            font-size: 1.2rem;
            margin-bottom: 2px;
        }
        /* Hide default Streamlit footer types if needed */
    </style>
    """, unsafe_allow_html=True)
    
    # Simple columnar layout at bottom for buttons
    # Note: Streamlit buttons inside columns at bottom of flow
    # To truly fix to bottom, we need CSS hacking or just placing them at end of script
    pass

def navigate_to(page_key):
    st.session_state["v2_page"] = page_key
    # Sync radio button
    if page_key in NAV_OPTIONS:
        st.session_state["v2_nav_radio"] = NAV_OPTIONS[page_key]
    else:
        st.session_state["v2_nav_radio"] = None

def render_budget_cards(df, services, supabase, is_mobile=False):
    budgets = services.get_budgets(supabase)
    tz = pytz.timezone("Asia/Shanghai")
    now = pd.Timestamp.now(tz=tz)
    this_month_str = now.strftime("%Y-%m")
    
    user = st.session_state.get("user")
    user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
    
    # Date Calculations for Timeline
    days_in_month = now.days_in_month
    current_day = now.day
    days_left = days_in_month - current_day
    time_pct = (current_day / days_in_month) * 100
    
    # Start and End of month strings
    start_str = now.replace(day=1).strftime("%b 1")
    end_str = now.replace(day=days_in_month).strftime("%b %d")
    
    if budgets:
        # Prepare data
        df_budget_calc = df.copy()
        if "月(yyyy-mm)" in df_budget_calc.columns:
            df_budget_calc = df_budget_calc[df_budget_calc["月(yyyy-mm)"] == this_month_str]
        
        # Grid layout
        cols = st.columns(2) 
        icon_map = {
            "餐饮": "🍔", "日用品": "🛒", "交通": "🚗", "服饰": "👔", 
            "医疗": "💊", "娱乐": "🎮", "居住": "🏠", "其他": "📦"
        }

        for i, b in enumerate(budgets):
            with cols[i % 2]:
                spent = df_budget_calc[df_budget_calc["分类"] == b["category"]]["有效金额"].sum() if "分类" in df_budget_calc.columns else 0
                limit = b["amount"]
                left = limit - spent
                
                pct = spent / limit if limit > 0 else 0
                pct_clamped = min(pct, 1.0) * 100
                
                # Daily Advice
                if days_left > 0 and left > 0:
                    daily_budget = left / days_left
                    advice_text = f"建议每日消费 <span style='color:#fff; font-weight:600;'>{user_currency}{daily_budget:.0f}</span>，还剩 {days_left} 天"
                elif left <= 0:
                    advice_text = "⚠️ 预算已超支 (Over Budget)"
                else: # Last day
                    advice_text = f"最后一天，剩余预算 {user_currency}{left:.0f}"

                # Health & Color Determination
                # Logic: Progressive Gradient based on usage pct
                if pct > 1.0:
                    bar_color = "linear-gradient(90deg, #EB5757, #FF4B2B)" # Red (Over)
                    text_color = "#FF4B4B"
                elif pct > 0.8:
                    bar_color = "linear-gradient(90deg, #F2994A, #F2C94C)" # Orange (Warning)
                    text_color = "#F2C94C"
                elif pct > 0.5:
                    bar_color = "linear-gradient(90deg, #2F80ED, #56CCF2)" # Light Blue (Normal)
                    text_color = "#56CCF2"
                else:
                    bar_color = "linear-gradient(90deg, #0f2027, #2F80ED)" # Dark Blue to Blue (Low)
                    text_color = "#2F80ED"
                
                icon = icon_map.get(b["category"], "💰")
                
                # --- RESPONSIVE STYLE & HTML GENERATION ---
                if is_mobile:
                    # Mobile: Icon Left, Text Right, Compact Fonts, Extra Padding
                    padding_top = "40px"
                    
                    style_css = """
.bc-cat-row { display: flex; justify-content: flex-start; align-items: center; gap: 12px; margin-bottom: 4px; }
.bc-icon-box { 
    background: rgba(255,255,255,0.15); 
    width: 48px; height: 48px; border-radius: 14px; 
    display: flex; align-items: center; justify-content: center; 
    backdrop-filter: blur(4px);
}
.bc-amount-big { font-size: 0.8rem; font-weight: 700; display: inline-block; opacity: 0.9; }
.bc-amount-sub { font-size: 1.4rem; font-weight: 700; display: inline-block; opacity: 1.0; }
"""
                    
                    top_html = f"""
<div class="bc-top">
<div class="bc-cat-row">
<div class="bc-icon-box" style="font-size: 1.5rem;">{icon}</div>
<div class="bc-cat-name">{b['category']}</div>
</div>
<div style="text-align: right; margin-top: 4px;">
<span class="bc-amount-big">{user_currency}{left:,.0f}</span>
<span class="bc-amount-sub"> left of {user_currency}{limit:,.0f}</span>
</div>
</div>
"""
                else:
                    # Desktop: Icon Right, Text Left, Big Fonts, Standard Padding
                    padding_top = "20px"
                    
                    style_css = """
.bc-cat-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.bc-icon-box { 
    background: rgba(255,255,255,0.15); 
    width: 60px; height: 60px; border-radius: 18px; 
    display: flex; align-items: center; justify-content: center; 
    backdrop-filter: blur(4px);
}
.bc-amount-big { font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
.bc-amount-sub { font-size: 0.9rem; opacity: 0.8; font-weight: 500; }
"""
                    
                    top_html = f"""
<div class="bc-top">
<div class="bc-cat-row">
<div class="bc-cat-name">{b['category']}</div>
<div class="bc-icon-box" style="font-size: 1.8rem;">{icon}</div>
</div>
<div class="bc-amount-big">{user_currency}{left:,.0f}</div>
<div class="bc-amount-sub">left of {user_currency}{limit:,.0f}</div>
</div>
"""

                # Final HTML construction (No indentation to prevent code block rendering)
                card_html = f"""
<div class="budget-card-container">
{top_html}
<div class="bc-bottom">
<div class="timeline-row">
<span>{start_str}</span>
<!-- Percentage moved to progress bar -->
<span>{end_str}</span>
</div>
<div class="track-container">
<div class="track-bg"></div>
<div class="track-fill" style="width: {pct_clamped}%; background: {bar_color};">
<div class="track-text-overlay">{int(pct_clamped)}%</div>
</div>
<div class="marker-today" style="left: {time_pct}%;">
<div class="marker-bubble">Today</div>
<div class="marker-line"></div>
</div>
</div>
<div class="bc-advice">
{advice_text}
</div>
</div>
</div>
"""
                
                # Render Style
                st.markdown(f"""
<style>
    .budget-card-container {{
        border-radius: 24px;
        overflow: hidden;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-family: 'Inter', sans-serif;
    }}
    .bc-top {{
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 10px 24px;
        color: white;
        position: relative;
    }}
    
    .bc-cat-name {{ font-size: 1.4rem; font-weight: 700; opacity: 0.95; }}

    /* Injected Dynamic Styles */
    {style_css}
    
    .bc-bottom {{
        background: #181818;
        padding: {padding_top} 24px 20px 24px;
        border-top: 1px solid rgba(255,255,255,0.05);
    }}
    .timeline-row {{
        display: flex; justify-content: space-between;
        color: #666; font-size: 0.75rem; font-weight: 600;
        align-items: center;
        margin-bottom: 15px;
    }}
    .track-container {{
        position: relative;
        height: 70px; /* Increased space for 40px bar */
        margin-bottom: 0px;
        /* Removed flex to rely on absolute positioning */
    }}
    .track-bg {{
        position: absolute; left: 0; right: 0; top: 50%; transform: translateY(-50%);
        height: 40px; background: #333; border-radius: 20px; /* 40px thick */
    }}
    .track-fill {{
        position: absolute; left: 0; top: 50%; transform: translateY(-50%);
        height: 40px; border-radius: 20px; /* 40px thick */
        /* width and background moved to inline style */
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
        transition: width 0.5s ease;
        z-index: 1;
    }}
    .marker-today {{
        position: absolute; top: 0; 
        /* left moved to inline style */
        transform: translateX(-50%);
        display: flex; flex-direction: column; align-items: center;
        z-index: 2;
        height: 50%; /* End at the vertical center (middle of the bar) */
        pointer-events: none;
    }}
    .marker-bubble {{
        background: #fff; color: #000;
        padding: 2px 6px; border-radius: 6px;
        font-size: 0.65rem; font-weight: 800;
        margin-bottom: 2px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        line-height: 1;
    }}
    .marker-line {{
        width: 2px; background: #fff; opacity: 0.8;
        flex-grow: 1; /* Stretch to fill the 50% height */
    }}
    
    .track-text-overlay {{
        position: absolute; left: 50%; top: 50%; 
        transform: translate(-50%, -50%);
        color: #fff;
        font-weight: 800;
        font-size: 0.9rem;
        z-index: 3;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8);
        pointer-events: none;
        white-space: nowrap;
    }}
    
    .bc-advice {{
        text-align: center; color: #888; font-size: 0.8rem; margin-top: 15px;
    }}
</style>
""", unsafe_allow_html=True)
                
                # Render HTML Structure using st.markdown with unsafe_allow_html=True but strictly NO indentation
                st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("暂无预算配置 (No Budgets Set)")

def render_top_navigation(df, services, supabase, is_mobile=False):
    if is_mobile:
        render_unified_kpi_card(df, services, supabase)
        return

    # KPIs Calculation
    tz = pytz.timezone("Asia/Shanghai")
    this_month = pd.Timestamp.now(tz=tz).strftime("%Y-%m")
    
    if "月(yyyy-mm)" in df.columns:
        month_df = df[df["月(yyyy-mm)"] == this_month]
        month_total = month_df["有效金额"].sum()
        count = len(month_df)
    else:
        month_total = 0
        count = 0
        
    budgets = services.get_budgets(supabase)
    budget_total = sum([b["amount"] for b in budgets])
    
    # Calculate Remaining Budget correctly: Sum of (Budget - Spent) for each category
    # This prevents non-budgeted spending from affecting the "Remaining Budget" KPI
    left = 0
    if budgets:
        # Prepare data for calculation
        df_calc = df.copy()
        if "月(yyyy-mm)" in df_calc.columns:
            df_calc = df_calc[df_calc["月(yyyy-mm)"] == this_month]
            
        for b in budgets:
            spent = df_calc[df_calc["分类"] == b["category"]]["有效金额"].sum() if "分类" in df_calc.columns else 0
            remaining = b["amount"] - spent
            left += remaining
    else:
        left = 0
    
    subs = services.get_recurring_rules(supabase)
    active_subs = len(subs)

    user = st.session_state.get("user")
    user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"

    # Render Clickable KPI Cards with Ghost Button Strategy (Overlay)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div id="kpi-card-1" class="kpi-card-visual kpi-blue">
            <div class="kpi-title">📅 本月支出 (Month)</div>
            <div class="kpi-value">{user_currency}{month_total:,.2f}</div>
            <div class="kpi-meta">{count} 笔交易</div>
        </div>
        """, unsafe_allow_html=True)
        target_page = "Dashboard" if is_mobile else "Transactions"
        st.button(" ", key="btn_trans_ghost", use_container_width=True, on_click=navigate_to, args=(target_page,))

    with c2:
        st.markdown(f"""
        <div id="kpi-card-2" class="kpi-card-visual kpi-purple">
            <div class="kpi-title">💰 剩余预算 (Left)</div>
            <div class="kpi-value">{user_currency}{left:,.2f}</div>
            <div class="kpi-meta">总额: {user_currency}{budget_total:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.button(" ", key="btn_analysis_ghost", use_container_width=True, on_click=navigate_to, args=("Analysis",))

    with c3:
        st.markdown(f"""
        <div id="kpi-card-3" class="kpi-card-visual kpi-dark">
            <div class="kpi-title">🔄 活跃订阅 (Subs)</div>
            <div class="kpi-value">{active_subs}</div>
            <div class="kpi-meta">固定支出项目</div>
        </div>
        """, unsafe_allow_html=True)
        st.button(" ", key="btn_subs_ghost", use_container_width=True, on_click=navigate_to, args=("Subscriptions",))

def render_heatmap(supabase, is_mobile=False):
    # Load data for 6 months (~182 days)
    data = services.get_daily_activity(supabase, days=200) 
    if not data: return
    
    tz = pytz.timezone("Asia/Shanghai")
    today = datetime.datetime.now(tz).date()
    
    # Responsive Settings
    if is_mobile:
        days_to_show = 105 # 15 weeks
        cell_size = "14px"
        gap = "2px"
        heatmap_height = "auto"
        heatmap_justify = "flex-start"
    else:
        days_to_show = 182 # 26 weeks
        cell_size = "20px"
        gap = "3px"
        heatmap_height = "280px" # Force height to match Trend Card
        heatmap_justify = "space-between"

    start_date = today - datetime.timedelta(days=days_to_show - 1)
    
    cells = []
    months = []
    last_month = ""
    
    for i in range(days_to_show):
        d = start_date + datetime.timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        amount = data.get(d_str, 0)
        
        # Color scale (Money based)
        if amount == 0: color = "#2d333b"
        elif amount <= 50: color = "#0e4429"
        elif amount <= 200: color = "#006d32"
        elif amount <= 500: color = "#26a641"
        else: color = "#39d353"
        
        user = st.session_state.get("user")
        user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
        
        cells.append(f'<div class="heatmap-cell" style="background-color:{color};" title="{d_str}: {user_currency}{amount:,.0f}"></div>')
        
        # Track months for labels
        m = d.strftime("%b")
        if m != last_month:
            months.append(m)
            last_month = m
            
    # Labels
    labels_html = "".join([f"<span>{m}</span>" for m in months])

    grid_html = f"""
    <style>
        /* Internal styling only - Container is handled by Streamlit */
        .heatmap-internal {{
            width: 100%;
            display: flex; flex-direction: column;
            height: {heatmap_height}; 
            justify-content: {heatmap_justify};
        }}
        .heatmap-inner-wrapper {{
            width: 100%;
            overflow-x: auto;
            margin-top: 3px;
        }}
        .heatmap-grid {{
            display: grid;
            grid-template-rows: repeat(7, {cell_size}); /* Dynamic cell size */
            grid-auto-flow: column;
            gap: {gap};
            margin-bottom: 8px;
        }}
        .heatmap-cell {{
            width: {cell_size};
            height: {cell_size};
            border-radius: 4px;
        }}
        .heatmap-labels {{
            display: flex;
            justify-content: space-between;
            color: #888;
            font-size: 0.8rem;
            padding: 0 2px;
            font-weight: 500;
        }}
    </style>
    <div class="heatmap-internal">
        <div class="kpi-title" style="margin-bottom:5px;">🔥 活跃分布 (Activity)</div>
        <div class="heatmap-inner-wrapper">
            <div>
                <div class="heatmap-grid">
                    {''.join(cells)}
                </div>
                <div class="heatmap-labels">
                    {labels_html}
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(grid_html, unsafe_allow_html=True)

def render_desktop_dashboard(df, services, supabase, is_mobile=False):
    render_top_navigation(df, services, supabase, is_mobile=is_mobile)
    
    # Heatmap & Trend Chart Side-by-Side (50/50 Split)
    c_heat, c_trend = st.columns(2)
    
    with c_heat:
        # Wrap Heatmap in Streamlit Container for consistent styling
        with st.container(border=True):
            render_heatmap(supabase)
        
    with c_trend:
        # Wrap Trend in Streamlit Container for consistent styling
        with st.container(border=True):
            st.markdown('<div class="kpi-title" style="margin-bottom:15px;">📉 支出趋势 (Trend)</div>', unsafe_allow_html=True)
            
            tz = pytz.timezone("Asia/Shanghai")
            this_month = pd.Timestamp.now(tz=tz).strftime("%Y-%m")
            
            user = st.session_state.get("user")
            user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
            
            if "月(yyyy-mm)" in df.columns:
                daily_trend = df[df["月(yyyy-mm)"] == this_month].groupby("日期")["有效金额"].sum().reset_index()
                if not daily_trend.empty:
                    fig = px.area(daily_trend, x="日期", y="有效金额", title="", color_discrete_sequence=["#56CCF2"])
                    fig.update_traces(hovertemplate="%{x}<br>有效金额: " + user_currency + "%{y:,.2f}<extra></extra>")
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(showgrid=False, tickfont=dict(color="#888")),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#888")),
                        height=230 # Reduced to 230 to match Heatmap 270px total
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"staticPlot": is_mobile})
                else:
                    st.info("本月暂无数据")
            else:
                 st.info("无数据")

    # Recent Records (Grouped)
    st.markdown('<div class="kpi-title" style="margin-top:20px; margin-bottom:15px;">🕒 最近记录 (Recent)</div>', unsafe_allow_html=True)
    
    if not df.empty:
        # Sort and Group
        df_sorted = df.sort_values(by=["date", "id"], ascending=[False, False]).head(20)
        
        tz = pytz.timezone("Asia/Shanghai")
        now_cn = datetime.datetime.now(tz)
        today_str = now_cn.strftime("%Y-%m-%d")
        yesterday_str = (now_cn - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        current_group = None
        
        user = st.session_state.get("user")
        user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
        
        for _, row in df_sorted.iterrows():
            d_str = pd.to_datetime(row["日期"]).strftime("%Y-%m-%d")
            
            # Determine Group Header
            if d_str == today_str: group_name = "Today"
            elif d_str == yesterday_str: group_name = "Yesterday"
            else: group_name = pd.to_datetime(d_str).strftime("%A, %B %d")
            
            if group_name != current_group:
                st.markdown(f'<div style="color:#888; font-size:0.85rem; margin-top:15px; margin-bottom:5px;">{group_name}</div>', unsafe_allow_html=True)
                current_group = group_name
            
            # Icon mapping
            cat = row["分类"]
            icon_map = {
                "餐饮": "🍔", "日用品": "🛒", "交通": "🚗", "服饰": "👔", 
                "医疗": "💊", "娱乐": "🎮", "居住": "🏠", "其他": "📦"
            }
            icon = icon_map.get(cat, "💰")
            
            # Render Row
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:12px; background:#121212; border-radius:12px; margin-bottom:8px; border:1px solid #2A2A2A;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="width:40px; height:40px; border-radius:50%; background:#1E1E1E; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">
                        {icon}
                    </div>
                    <div>
                        <div style="color:#eee; font-weight:500;">{row['项目']}</div>
                        <div style="color:#666; font-size:0.8rem;">{cat} • {row.get('备注','')}</div>
                    </div>
                </div>
                <div style="color:#FF4B4B; font-weight:600;">-{user_currency}{row['有效金额']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.caption("无最近记录")
                
def render_analysis(df, services, supabase, is_mobile=False):
    render_top_navigation(df, services, supabase, is_mobile=is_mobile)
    st.header("深度分析")
    
    # === Budget Progress Section (Visuals & Link to Management) ===
    with st.container(border=True):
        c_title, c_link = st.columns([5, 1])
        with c_title:
            st.subheader("📊 预算详情 (Budget Breakdown)")
        with c_link:
            st.button(
                "⚙️ 管理", 
                key="goto_budget_manage", 
                help="管理预算",
                use_container_width=True,
                on_click=navigate_to,
                args=("Budgets",)
            )
        
        render_budget_cards(df, services, supabase)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("分类占比 (Category)")
        if not df.empty and "分类" in df.columns:
             # Prepare Data with Icons
             icon_map = {
                "餐饮": "🍔", "日用品": "🛒", "交通": "🚗", "服饰": "👔", 
                "医疗": "💊", "娱乐": "🎮", "居住": "🏠", "其他": "📦"
             }
             
             df_pie = df.copy()
             df_pie["IconLabel"] = df_pie["分类"].apply(lambda x: f"{icon_map.get(x, '💰')} {x}")
             
             user = st.session_state.get("user")
             user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
             
             fig = px.pie(df_pie, names="IconLabel", values="有效金额", hole=0.6, 
                 color_discrete_sequence=["#2F80ED", "#56CCF2", "#6FCF97", "#F2C94C", "#BB6BD9", "#EB5757", "#9B51E0", "#2D9CDB"])
             fig.update_traces(
                 textinfo='percent+label', 
                 textposition='inside', 
                 textfont_color="white",
                 hovertemplate="%{label}<br>有效金额: " + user_currency + "%{value:,.2f}<extra></extra>"
             )
             fig.update_layout(
                 paper_bgcolor="rgba(0,0,0,0)", 
                 margin=dict(t=20, b=20, l=20, r=20), 
                 showlegend=False
             )
             fig.update_layout(
                 paper_bgcolor="rgba(0,0,0,0)", 
                 margin=dict(t=20, b=20, l=20, r=20), 
                 showlegend=False
             )
             st.plotly_chart(fig, use_container_width=True, config={"staticPlot": is_mobile})
             
    with c2:
        st.subheader("月度对比 (Monthly)")
        if not df.empty and "月(yyyy-mm)" in df.columns:
            user = st.session_state.get("user")
            user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
            
            monthly = df.groupby("月(yyyy-mm)")["有效金额"].sum().reset_index()
            fig = px.bar(monthly, x="月(yyyy-mm)", y="有效金额", text_auto=".2s")
            fig.update_traces(
                marker_color='#2F80ED', 
                marker_line_width=0, 
                textfont_color="#fff",
                hovertemplate="%{x}<br>有效金额: " + user_currency + "%{y:,.2f}<extra></extra>"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#888")),
                xaxis=dict(tickfont=dict(color="#888"))
            )
            st.plotly_chart(fig, use_container_width=True, config={"staticPlot": is_mobile})

def render_subscriptions(df, services, supabase, is_mobile=False):
    render_top_navigation(df, services, supabase, is_mobile=is_mobile)
    st.header("订阅管理 (Subscriptions)")
    
    rules = services.get_recurring_rules(supabase)
    if not rules:
        st.info("暂无订阅信息，请点击右上角 '+' 按钮添加。")
        rules = []

    user = st.session_state.get("user")
    user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"

    # 1. Summary Cards
    total_monthly = sum([r["amount"] for r in rules if r["frequency"] == "Monthly"]) + \
                    sum([r["amount"] * 4 for r in rules if r["frequency"] == "Weekly"]) + \
                    sum([r["amount"] / 12 for r in rules if r["frequency"] == "Yearly"])
                    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("月度固定支出 (Est. Monthly)", f"{user_currency}{total_monthly:,.2f}")
    with c2:
        st.metric("活跃订阅数 (Active Subs)", f"{len(rules)}")
        
    st.divider()
    
    # 2. Add New Subscription
    with st.expander("➕ 添加新订阅 (Add New Subscription)", expanded=False):
        with st.form("sub_page_add"):
            c_name, c_cat = st.columns(2)
            r_name = c_name.text_input("名称 (Name)", placeholder="Netflix, Spotify...")
            r_cat = c_cat.selectbox("分类", CATEGORIES)
            
            c_amt, c_freq = st.columns(2)
            r_amt = c_amt.number_input(f"金额 ({user_currency})", min_value=0.0, step=1.0)
            r_freq = c_freq.selectbox("周期", ["Monthly", "Weekly", "Yearly"])
            
            tz = pytz.timezone("Asia/Shanghai")
            r_date = st.date_input("首次/下次扣款日期", value=pd.Timestamp.now(tz=tz))
            
            if st.form_submit_button("确认添加", type="primary", use_container_width=True):
                services.add_recurring(supabase, st.session_state["user"].id, r_name, r_amt, r_cat, r_freq, r_date)
                st.success(f"已添加: {r_name}")
                st.rerun()

    # 3. List
    st.subheader("订阅列表")
    if rules:
        df_rules = pd.DataFrame(rules)
        df_rules["delete"] = False
        
        r_cfg = {
            "name": st.column_config.TextColumn("名称", required=True, width="medium"),
            "amount": st.column_config.NumberColumn(f"金额 ({user_currency})", format=f"{user_currency}%.2f", width="small"),
            "day": st.column_config.NumberColumn("日/W", min_value=0, max_value=31, width="small", help="每月几号或每周几"),
            "delete": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
            "category": st.column_config.SelectboxColumn("分类", options=CATEGORIES, width="small"),
            "frequency": st.column_config.SelectboxColumn("周期", options=["Monthly", "Weekly", "Yearly"], width="small"),
            "id": None, "user_id": None, "active": None, "created_at": None, "last_triggered": None
        }

        edited_r = st.data_editor(
            df_rules[["id", "name", "amount", "frequency", "day", "category", "delete"]], 
            column_config=r_cfg, 
            use_container_width=True, 
            hide_index=True, 
            key="sub_page_editor", 
            num_rows="dynamic"
        )
        
        col_btn, _ = st.columns([1, 2])
        if col_btn.button("💾 保存更改 (Save Changes)", type="primary", use_container_width=True):
                 # Deletes
                 to_delete_r = edited_r[edited_r["delete"] == True]
                 for idx, row in to_delete_r.iterrows(): services.delete_recurring(supabase, row["id"])
                 
                 curr_r_ids = set(df_rules["id"].tolist())
                 new_r_ids = set([r["id"] for i, r in edited_r.iterrows() if "id" in r and pd.notna(r["id"])])
                 for d_id in (curr_r_ids - new_r_ids): services.delete_recurring(supabase, d_id)

                 # Updates
                 for idx, row in edited_r.iterrows():
                     if row["delete"] == True: continue
                     if "id" in row and pd.notna(row["id"]):
                          try: 
                              services.update_recurring(supabase, row["id"], {
                                  "name": row["name"], 
                                  "amount": float(row["amount"]), 
                                  "day": int(row["day"]),
                                  "frequency": row["frequency"],
                                  "category": row["category"]
                              })
                          except: pass
                 
                 st.success("✅ 订阅已更新")
                 time.sleep(1)
                 st.cache_data.clear()
                 st.rerun()

def render_transactions(df, services, supabase, is_mobile=False):
    render_top_navigation(df, services, supabase, is_mobile=is_mobile)
    st.header("所有交易")
    
    # Filter Toolbar
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1: 
        filter_cat = st.multiselect("分类筛选", options=CATEGORIES, placeholder="全部分类")
    with c2:
        search = st.text_input("搜索", placeholder="搜索项目...")
        
    df_show = df.copy()
    if filter_cat:
        df_show = df_show[df_show["分类"].isin(filter_cat)]
    if search:
        df_show = df_show[df_show["项目"].str.contains(search, case=False) | df_show["备注"].str.contains(search, case=False)]
        
    # Data Editor
    st.caption(f"共找到 {len(df_show)} 条记录")
    
    edit_cols = ["删除", "日期", "项目", "金额", "分类", "备注", "id"]
    df_show["删除"] = False
    
    user = st.session_state.get("user")
    user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"

    col_cfg = {
        "删除": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
        "日期": st.column_config.DateColumn("日期", width="medium"),
        "项目": st.column_config.TextColumn("项目", width="large"),
        "金额": st.column_config.NumberColumn(f"金额 ({user_currency})", format=f"{user_currency}%.2f", width="small"),
        "分类": st.column_config.SelectboxColumn("分类", options=CATEGORIES, width="medium"),
        "备注": st.column_config.TextColumn("备注", width="large"),
        "id": None
    }
    
    with st.form("clean_editor"):
        edited = st.data_editor(
            df_show[edit_cols], 
            column_config=col_cfg, 
            hide_index=True, 
            use_container_width=True, 
            num_rows="fixed",
            height=600
        )
        if st.form_submit_button("💾 保存更改 (Save Changes)", type="primary"):
            # Update Logic (Simplified reuse)
            to_delete = edited[edited["删除"] == True]
            for id_val in to_delete["id"]: services.delete_expense(supabase, id_val)
            
            st.success("操作已提交")
            time.sleep(1)
            st.cache_data.clear()
            st.rerun()

def render_chat(df, services, supabase, user, is_mobile=False):
    render_top_navigation(df, services, supabase, is_mobile=is_mobile)
    
    if not is_mobile:
        st.header("AI 智能助手")
        st.caption("告诉我你花了什么钱，或者问我财务问题。")
    else:
        # Minimal header for mobile to save vertical space
        st.markdown("<div style='margin-top: -10px; margin-bottom: 10px; font-weight: bold; font-size: 1.1rem;'>🤖 AI 助手</div>", unsafe_allow_html=True)

    if is_mobile:
        st.markdown("""
        <style>
            [data-testid="stChatInput"] {
                bottom: 42px !important; /* Lifted by an additional 5px */
                width: calc(100% - 8px) !important; /* make it narrower, centering it */
                left: 50% !important;
                transform: translateX(-50%) !important;
            }
            /* Forcefully reduce chat input overall height */
            [data-testid="stChatInput"] > div {
                min-height: 38px !important;
                padding: 4px 12px !important;
            }
            [data-testid="stChatInput"] textarea {
                min-height: 30px !important; 
                padding-top: 6px !important;
                padding-bottom: 6px !important;
            }
            [data-testid="stChatInput"] button {
                height: 30px !important;
                min-height: 30px !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # Allow natural page scrolling on mobile so the first message natively appears at the top
    if is_mobile:
        chat_container = st.container(border=True)
    else:
        chat_container = st.container(height=500, border=True)
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 准备好记账了吗？"}]
        
    user_avatar = user.user_metadata.get("avatar_url") if user.user_metadata.get("avatar_url") else "https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123"

    with chat_container:
        for msg in st.session_state.messages:
             role = msg["role"]
             avatar = "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput" if role == "assistant" else user_avatar
             st.chat_message(role, avatar=avatar).write(msg["content"])

    if prompt := st.chat_input("例如：打车 50，超市买菜 120..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user", avatar=user_avatar).write(prompt)
        
        with chat_container:
             with st.chat_message("assistant", avatar="https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput"):
                 ph = st.empty()
                 ph.write("Thinking...")
                 
                 # Fetch Context for AI
                 budgets = services.get_budgets(supabase)
                 subs = services.get_recurring_rules(supabase)
                 
                 user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
                 
                 result = expense_chat.process_user_message(prompt, df, budgets, subs, user_currency=user_currency)
                 reply = "Completed."
                 
                 intent = result.get("type", "chat")
                 
                 # 1. RECORD
                 if intent == "record":
                     recs = result.get("records", []) or ([result] if "item" in result else [])
                     payloads = []
                     names = []
                     for r in recs:
                         payloads.append({
                             "user_id": user.id, "date": r.get("date"), "item": r.get("item"), 
                             "amount": r.get("amount"), "category": r.get("category", "其他"),
                             "note": r.get("note", ""), "source": "chat_v2"
                         })
                         names.append(r.get("item"))
                     if payloads:
                         services.add_expenses_batch(supabase, payloads)
                         reply = f"✅ 已记录: {', '.join(names)}"
                         st.session_state["data_changed"] = True
                     else:
                         reply = "未识别到内容"

                 # 2. CHAT
                 elif intent == "chat":
                     reply = result.get("reply", "...")

                 # 3. DELETE EXPENSE
                 elif intent == "delete":
                     eid = result.get("id")
                     if eid:
                         services.delete_expense(supabase, eid)
                         reply = result.get("reply", "已删除")
                         st.session_state["data_changed"] = True
                     else:
                         reply = "未找到对应记录"

                 # 4. UPDATE EXPENSE
                 elif intent == "update":
                     eid = result.get("id")
                     updates = result.get("updates")
                     if eid and updates:
                         services.update_expense(supabase, eid, updates)
                         reply = result.get("reply", "已更新")
                         st.session_state["data_changed"] = True
                     else:
                         reply = "更新失败，缺少信息"

                 # 5. ADD BUDGET
                 elif intent == "budget_add":
                     # category, amount
                     cat = result.get("category")
                     amt = result.get("amount")
                     if cat and amt:
                         # Check if budget exists for this category
                         existing_budget = next((b for b in budgets if b["category"] == cat), None)
                         
                         if existing_budget:
                             # Update existing
                             services.update_budget(supabase, existing_budget["id"], {"amount": float(amt)})
                             reply = f"已更新 {cat} 预算为 {amt} 元 (原为 {existing_budget['amount']} 元)"
                         else:
                             # Add new
                             icon_map = {"餐饮":"🍔", "交通":"🚗", "日用品":"🛒", "服饰":"👔", "娱乐":"🎮", "医疗":"💊", "居住":"🏠", "其他":"📦"}
                             icon = icon_map.get(cat, "💰")
                             services.add_budget(supabase, user.id, f"{cat}预算", cat, amt, "#2F80ED", icon)
                             reply = result.get("reply", f"已设置 {cat} 预算")
                         
                         st.session_state["data_changed"] = True
                     else:
                         reply = "设置预算失败，缺少分类或金额"

                 # 6. DELETE BUDGET
                 elif intent == "budget_delete":
                     bid = result.get("id")
                     if bid:
                         services.delete_budget(supabase, bid)
                         reply = result.get("reply", "已删除预算")
                         st.session_state["data_changed"] = True
                     else:
                         reply = "未找到该预算"

                 # 7. ADD RECURRING
                 elif intent == "recurring_add":
                     # name, amount, category, frequency, day
                     try:
                         # Default day calculation if not provided is hard in prompt, usually prompt gives start_date
                         # We need to parse start_date to get day/weekday
                         start_date_str = result.get("start_date")
                         if start_date_str:
                             s_date = pd.to_datetime(start_date_str)
                         else:
                             s_date = pd.Timestamp.now()
                         
                         services.add_recurring(
                             supabase, user.id, 
                             result.get("name"), 
                             float(result.get("amount", 0)), 
                             result.get("category", "其他"), 
                             result.get("frequency", "Monthly"), 
                             s_date
                         )
                         reply = result.get("reply", "已添加订阅")
                         st.session_state["data_changed"] = True
                     except Exception as e:
                         reply = f"添加订阅失败: {e}"

                 # 8. DELETE RECURRING
                 elif intent == "recurring_delete":
                     rid = result.get("id")
                     if rid:
                         services.delete_recurring(supabase, rid)
                         reply = result.get("reply", "已删除订阅")
                         st.session_state["data_changed"] = True
                     else:
                         reply = "未找到该订阅"
                 
                 ph.write(reply)
                 st.session_state.messages.append({"role": "assistant", "content": reply})
                 
    if st.session_state.get("data_changed"):
        st.cache_data.clear()
        del st.session_state["data_changed"]
        st.rerun()

    st.divider()

    # Autofocus for Mobile Experience
    if is_mobile:
        components.html("""
            <script>
                function focusChat() {
                    const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (textArea) {
                        textArea.focus();
                    }
                }
                setTimeout(focusChat, 500);
            </script>
        """, height=0, width=0)

def render_budgets(df, services, supabase, user, is_mobile=False):
    render_top_navigation(df, services, supabase, is_mobile=is_mobile)
    st.header("预算管理 (Budgets)")
    
    user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
    
    # === 1. Budget Breakdown (Visuals) ===
    with st.container(border=True):
        st.subheader("📊 预算详情 (Budget Breakdown)")
        
        budgets = services.get_budgets(supabase)
        tz = pytz.timezone("Asia/Shanghai")
        this_month = pd.Timestamp.now(tz=tz).strftime("%Y-%m")
        
        if budgets:
            # Prepare data
            df_budget_calc = df.copy()
            if "月(yyyy-mm)" in df_budget_calc.columns:
                df_budget_calc = df_budget_calc[df_budget_calc["月(yyyy-mm)"] == this_month]
            
            # Grid layout for budgets
    # === 1. Budget Breakdown (Visuals) ===
    with st.container(border=True):
        st.subheader("📊 预算详情 (Budget Breakdown)")
        render_budget_cards(df, services, supabase)
    
    st.divider()

    # === 2. Budget Management (Edit) ===
    st.subheader("⚙️ 管理预算 (Manage)")
    
    # Add New Budget (Popover)
    with st.popover("➕ 添加新预算 (Add Budget)", use_container_width=True):
        with st.form("v2_add_budget_page"):
            b_cat = st.selectbox("分类", CATEGORIES, key="v2_b_cat_page")
            b_amt = st.number_input(f"限额 ({user_currency})", min_value=0, step=100, key="v2_b_amt_page")
            if st.form_submit_button("确认添加", type="primary", use_container_width=True):
                icon_map = {"餐饮":"🍔", "交通":"🚗", "日用品":"🛒", "服饰":"👔", "娱乐":"🎮", "医疗":"💊", "居住":"🏠", "其他":"📦"}
                icon = icon_map.get(b_cat, "💰")
                services.add_budget(supabase, user.id, f"{b_cat}预算", b_cat, b_amt, "#2F80ED", icon)
                st.rerun()

    # List & Edit Budgets
    cur_budgets = services.get_budgets(supabase)
    if cur_budgets:
        df_budgets = pd.DataFrame(cur_budgets)
        if "amount" in df_budgets.columns:
            df_budgets["amount"] = pd.to_numeric(df_budgets["amount"], errors="coerce").fillna(0)
        
        df_budgets["delete"] = False
        
        b_cfg = {
            "category": st.column_config.SelectboxColumn("分类", options=CATEGORIES, required=True, width="medium"),
            "amount": st.column_config.NumberColumn(f"限额 ({user_currency})", min_value=0, step=100, format=f"{user_currency}%d"),
            "delete": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
            "name": None, "id": None, "user_id": None, "icon": None, "color": None, "created_at": None
        }
        
        edited_b = st.data_editor(
            df_budgets,
            column_config=b_cfg,
            use_container_width=True,
            hide_index=True,
            key="v2_budget_editor_page",
            num_rows="dynamic"
        )
        
        if st.button("💾 保存预算 (Save Budgets)", key="v2_save_budgets_page", type="primary", use_container_width=True):
            # Handle Deletes
            to_delete = edited_b[edited_b["delete"] == True]
            for idx, row in to_delete.iterrows():
                    if "id" in row and pd.notna(row["id"]): services.delete_budget(supabase, row["id"])
            
            # Implicit Deletes
            current_ids = set(df_budgets["id"].tolist())
            new_ids = set([r["id"] for i, r in edited_b.iterrows() if "id" in r and pd.notna(r["id"])])
            for d_id in (current_ids - new_ids): services.delete_budget(supabase, d_id)

            # Updates
            for idx, row in edited_b.iterrows():
                if row["delete"] == True: continue
                if "id" in row and pd.notna(row["id"]):
                        try:
                            services.update_budget(supabase, row["id"], {"category": row["category"], "amount": float(row["amount"])})
                        except: pass
            
            st.success("✅ 预算已更新")
            time.sleep(1)
            st.cache_data.clear()
            st.rerun()

def render_settings(supabase, user, is_mobile=False):
    if is_mobile:
        st.markdown("""
        <style>
            /* Mobile Settings Polish */
            /* Left-align specific sections based on the request */
            h2 { font-size: 1.4rem !important; margin-bottom: 5px !important; text-align: left !important; color: #eee; }
            [data-testid="stCaptionContainer"] p { font-size: 0.85rem !important; color: #aaa !important; text-align: left !important; margin-bottom: 16px !important; line-height: 1.4; }
            h3 { font-size: 1.15rem !important; margin-top: 10px !important; text-align: left !important; }
            
            /* Compact Info Cards */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: 1px solid rgba(255,255,255,0.05) !important;
                background: #151515 !important;
                border-radius: 20px !important;
                padding: 16px !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
                margin-bottom: 10px;
            }
            
            /* Customizing the logout button to look destructive/red */
            button[kind="secondary"] { 
                border: 1px solid rgba(255,59,48,0.4) !important; 
                background: rgba(255,59,48,0.1) !important; 
                color: #ff4b4b !important; 
                border-radius: 16px !important;
                font-weight: 700 !important;
                padding: 24px 0 !important;
                font-size: 1.1rem !important;
                box-shadow: 0 4px 10px rgba(255,59,48,0.1);
            }
            button[kind="secondary"]:hover {
                background: rgba(255,59,48,0.2) !important; 
            }
            
            /* Styling "Browse files" Button to look like a Folder Upload */
            [data-testid="stFileUploader"] section {
                display: flex;
                flex-direction: row;
                align-items: center;
                gap: 12px;
            }
            
            /* Insert folder icon as a flex item BEFORE the button */
            [data-testid="stFileUploader"] section::before {
                content: "📁";
                font-size: 1.8rem;
                display: block;
            }
            
            [data-testid="stFileUploader"] button {
                background: linear-gradient(135deg, #f2c94c 0%, #f2994a 100%) !important;
                color: #222 !important;
                border: none !important;
                border-radius: 12px !important;
                font-weight: 700 !important;
                padding: 8px 16px !important;
                box-shadow: 0 4px 10px rgba(242, 169, 74, 0.3) !important;
                margin: 0 !important;
            }
            
            [data-testid="stFileUploader"] button * {
                 display: none !important; /* Hide default icon and text spans inside the button */
            }
            
            [data-testid="stFileUploader"] button::before {
                content: "上传头像图案";
                font-size: 0.95rem; /* Restore custom text size */
                visibility: visible !important; 
                display: block !important;
            }
            
            /* Softer divider */
            hr { margin-top: 2rem !important; margin-bottom: 2rem !important; border-color: rgba(255,255,255,0.1) !important; }
            
            /* Adjust uploader elements */
            [data-testid="stFileUploader"] { margin-top: -10px; padding-left: 10px; }
            [data-testid="stSelectbox"] { margin-top: -10px; }
        </style>
        """, unsafe_allow_html=True)

    st.header("⚙️ 账号与个人设置 (Settings)")
    st.caption("个性化您的控制台体验。")
    
    with st.container(border=True):
        # Create columns to display Avatar (Left) and Details (Right)
        col1, col2 = st.columns([1, 4])
        
        with col1:
            # Determine Avatar URL (custom or fallback)
            avatar_url = user.user_metadata.get("avatar_url")
            if not avatar_url:
                avatar_url = "https://api.dicebear.com/9.x/bottts/svg?seed=FinanceHelper&backgroundColor=00a6ff"
            st.image(avatar_url, width=60)
            
        with col2:
            st.write(f"**Email:** {user.email}")
            st.write(f"**User ID:** {user.id}")
        
    st.divider()
    
    st.subheader("🎨 个性化专属头像 (Avatar)")
    st.caption("更改左侧导航栏的专属头像。每位用户均可拥有独立的个人头像，不再与他人共享。")
    uploader_key = f"v2_user_logo_uploader_{st.session_state.get('avatar_upload_count', 0)}"
    uploaded_logo = st.file_uploader("上传您的专属 Logo (Upload Logo)", type=["png", "jpg", "jpeg"], key=uploader_key)
    if uploaded_logo:
         if uploaded_logo.size > 20 * 1024 * 1024:
             st.error("❌ 文件太大啦！请上传小于 20MB 的图片。")
         else:
             try:
                 # Upload to Supabase Storage
                 file_bytes = uploaded_logo.getvalue()
                 file_path = f"{user.id}/avatar.png"
                 content_type = uploaded_logo.type
                 
                 res = supabase.storage.from_("avatars").upload(
                     file_path, 
                     file_bytes, 
                     {"upsert": "true", "content-type": content_type}
                 )
                 
                 # Get Public URL and update metadata with cache-busting timestamp
                 base_public_url = supabase.storage.from_("avatars").get_public_url(file_path)
                 public_url = f"{base_public_url}?t={int(datetime.datetime.now().timestamp())}"
                 supabase.auth.update_user({"data": {"avatar_url": public_url}})
                 
                 # Refresh session state
                 auth_res = supabase.auth.get_user()
                 if auth_res and auth_res.user:
                     st.session_state["user"] = auth_res.user
                     
                 st.success("✅ 您的专属个人 Logo 已成功上传至云端并生效!")
                 # Removed time.sleep to avoid any possible time module scope issues
                 
                 # Dynamically change the uploader key to force Streamlit to completely unmount and reset it
                 st.session_state['avatar_upload_count'] = st.session_state.get('avatar_upload_count', 0) + 1
                 
                 st.rerun()
             except Exception as e:
                 st.error(f"上传失败: {e}")
         
    st.divider()
    
    st.subheader("💱 本地货币 (Currency)")
    st.caption("选择您记账时默认使用的货币符号。")
    cu_options = ["¥ (CNY人民币)", "$ (USD美元)", "€ (EUR欧元)", "£ (GBP英镑)", "₩ (KRW韩元)", "¥ (JPY日元)", "฿ (THB泰铢)"]
    
    current_currency = user.user_metadata.get("currency_symbol", "$ (USD美元)")
    # Fallback if somehow current_currency is not in options (e.g., just "$")
    if current_currency not in cu_options:
        # Try to match by symbol
        matched = next((opt for opt in cu_options if current_currency in opt), "¥ (CNY人民币)")
        current_currency = matched

    with st.form("currency_form"):
        selected_cu = st.selectbox("选择货币 (Select Currency)", options=cu_options, index=cu_options.index(current_currency))
        if st.form_submit_button("保存货币设置 (Save)", type="primary"):
            try:
                # We save the full string so the dropdown remembers exactly
                # But we'll extract the first character as the absolute symbol when rendering
                supabase.auth.update_user({"data": {"currency_symbol": selected_cu}})
                st.success(f"✅ 默认货币已更改为 {selected_cu.split(' ')[0]}")
                res = supabase.auth.get_user()
                if res and res.user:
                    st.session_state["user"] = res.user
                import time
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

    if not is_mobile:
        st.divider()
        st.subheader("🔑 OpenAI API Key (选填)")
        st.caption("填入您自己的 OpenAI API Key 以启用智能对话和自动记账功能。此 Key 仅保存在您的个人元数据中。")
        
        current_key = user.user_metadata.get("openai_api_key", "")
        with st.form("api_key_form"):
            new_key = st.text_input("OpenAI API Key (sk-...)", value=current_key, type="password")
            if st.form_submit_button("保存 Key (Save)", type="primary"):
                try:
                    # Update user metadata
                    supabase.auth.update_user({"data": {"openai_api_key": new_key}})
                    st.success("✅ OpenAI API Key 已安全保存至您的账号!")
                    res = supabase.auth.get_user()
                    if res and res.user:
                        st.session_state["user"] = res.user
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失败: {e}")

    st.divider()
    if st.button("🚪 注销退出 (Logout)", type="secondary", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state["session"] = None
        if "messages" in st.session_state:
            del st.session_state["messages"]
        st.rerun()

# ==========================================
# MAIN RENDER ENTRY
# ==========================================
# ==========================================
# MOBILE SPECIFIC COMPONENTS
# ==========================================
def render_unified_kpi_card(df, services, supabase):
    # KPIs Calculation
    tz = pytz.timezone("Asia/Shanghai")
    this_month = pd.Timestamp.now(tz=tz).strftime("%Y-%m")
    
    if "月(yyyy-mm)" in df.columns:
        month_df = df[df["月(yyyy-mm)"] == this_month]
        month_total = month_df["有效金额"].sum()
    else:
        month_total = 0
        
    budgets = services.get_budgets(supabase)
    
    left = 0
    if budgets:
        df_calc = df.copy()
        if "月(yyyy-mm)" in df_calc.columns:
            df_calc = df_calc[df_calc["月(yyyy-mm)"] == this_month]
        for b in budgets:
            spent = df_calc[df_calc["分类"] == b["category"]]["有效金额"].sum() if "分类" in df_calc.columns else 0
            left += (b["amount"] - spent)
            
    subs = services.get_recurring_rules(supabase)
    active_subs = len(subs)

    user = st.session_state.get("user")
    user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"

    # Kpi Card HTML Structure matching the design request (No indentation to prevent code block rendering)
    kpi_html = f"""
<style>
.kpi-card-v4 {{
    background: radial-gradient(circle at top left, #1a2a33 0%, #0d1216 100%);
    border-radius: 20px;
    padding: 24px;
    color: white;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.05);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}
.kpi-top-section {{ margin-bottom: 12px; }}
.kpi-label-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
.kpi-label-text {{ font-size: 0.9rem; color: #b0b0b0; font-weight: 400; letter-spacing: 0.5px; }}
.kpi-main-value {{ font-size: 2.8rem; font-weight: 700; color: #ffffff; line-height: 1.1; letter-spacing: -1px; }}
.kpi-divider {{ height: 1px; background-color: rgba(255,255,255,0.1); width: 100%; margin: 20px 0; }}
.kpi-bottom-section {{ display: flex; justify-content: space-between; align-items: flex-start; }}
.kpi-sub-item {{ display: flex; flex-direction: column; }}
.kpi-sub-label {{ font-size: 0.85rem; color: #b0b0b0; margin-bottom: 8px; height: 24px; display: flex; align-items: center; justify-content: flex-start; }}
.kpi-sub-value {{ font-size: 1.4rem; font-weight: 700; color: #ffffff; line-height: 1; text-align: left; }}
.text-right {{ align-items: flex-start; }}
</style>
<div class="kpi-card-v4">
    <div class="kpi-top-section">
        <div class="kpi-label-row">
             <span style="font-size: 1.1rem;">🗓️</span> <span>本月支出 (Month Spend)</span>
        </div>
        <div class="kpi-main-value">{user_currency}{month_total:,.2f}</div>
    </div>
    <div class="kpi-divider"></div>
    <div class="kpi-bottom-section">
        <div class="kpi-sub-item">
            <div class="kpi-sub-label" style="justify-content: flex-start;"><span style="font-size: 1rem; margin-right: 4px;">💰</span> 剩余预算 (Remaining)</div>
            <div class="kpi-sub-value" style="text-align: left;">{user_currency}{left:,.2f}</div>
        </div>
        <div class="kpi-sub-item text-right">
            <div class="kpi-sub-label" style="justify-content: flex-start;">活跃订阅 (Subs) <span style="font-size: 1rem; margin-left: 4px;">🔄</span></div>
            <div class="kpi-sub-value" style="text-align: left;">{active_subs}</div>
        </div>
    </div>
</div>
"""
    st.markdown(kpi_html, unsafe_allow_html=True)

def render_mobile_floating_bar():
    # Current Page
    current_page = st.session_state.get("v2_page", "Dashboard")
    
    # Hidden Streamlit Buttons (Workhorses)
    # We use a wrapper to help locate them
    st.markdown('<div class="nav-trigger-wrapper">', unsafe_allow_html=True)
    
    # Create a hidden button for each navigation option
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Toggle_Nav_Dashboard", key="btn_hidden_nav_dashboard"):
            st.session_state["v2_page"] = "Dashboard"
            st.rerun()
    with col2:
        if st.button("Toggle_Nav_SmartChat", key="btn_hidden_nav_smartchat"):
            st.session_state["v2_page"] = "Smart Chat"
            st.rerun()
    with col3:
        if st.button("Toggle_Nav_Settings", key="btn_hidden_nav_settings"):
            st.session_state["v2_page"] = "Settings"
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

    # Determine active states for styling
    is_home = "active" if current_page == "Dashboard" else ""
    is_chat = "active" if current_page == "Smart Chat" else ""
    is_settings = "active" if current_page == "Settings" else ""

    # Floating Bar using components.html (Iframe) to inject into PARENT DOM
    # This ensures position:fixed works relative to the viewport, not the iframe
    
    # We construct the JS payload
    js_payload = f"""
    <script>
        const parentDoc = window.parent.document;
        
        // 1. Hide the Toggle Buttons (Repeatedly to fight rerenders)
        function hideTrigger() {{
            const buttons = parentDoc.getElementsByTagName('button');
            for (let i = 0; i < buttons.length; i++) {{
                const text = buttons[i].innerText;
                if (text.includes("Toggle_Nav_Dashboard") || 
                    text.includes("Toggle_Nav_SmartChat") || 
                    text.includes("Toggle_Nav_Settings")) {{
                    buttons[i].style.position = "absolute";
                    buttons[i].style.top = "-9999px";
                    buttons[i].style.opacity = "0";
                    buttons[i].style.pointerEvents = "none";
                    buttons[i].style.zIndex = "-1";
                }}
            }}
        }}
        
        // 2. The click handler 
        parentDoc.defaultView.mobileNavClick = function(targetNav) {{
            const buttons = parentDoc.getElementsByTagName('button');
            let targetText = "";
            if (targetNav === 'home') targetText = "Toggle_Nav_Dashboard";
            if (targetNav === 'chat') targetText = "Toggle_Nav_SmartChat";
            if (targetNav === 'settings') targetText = "Toggle_Nav_Settings";
            
            for (let i = 0; i < buttons.length; i++) {{
                if (buttons[i].innerText.includes(targetText)) {{
                    buttons[i].click();
                    return;
                }}
            }}
        }};

        // 3. Inject Floating Bar Container
        const barId = 'my-mobile-float-bar-overlay';
        let barContainer = parentDoc.getElementById(barId);
        
        if (!barContainer) {{
            barContainer = parentDoc.createElement('div');
            barContainer.id = barId;
            parentDoc.body.appendChild(barContainer);
        }}
        
        // 4. Update Content (Re-render safe)
        barContainer.innerHTML = `
            <style>
                #my-mobile-float-bar-overlay .mobile-float-bar {{
                    position: fixed; bottom: 44px; /* Lifted by additional 3px */
                    left: 50%; transform: translateX(-50%);
                    width: 90%; max-width: 400px; height: 50px; /* Thinner */
                    background: rgba(30, 30, 30, 0.85); /* Slightly transparent dark background */
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 25px; /* Pill shape adapted to thinner height */
                    display: flex; align-items: center; justify-content: space-around;
                    padding: 0 10px; z-index: 999999;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
                    box-sizing: border-box;
                    font-family: 'Inter', sans-serif;
                    pointer-events: auto; /* Catch clicks */
                }}
                #my-mobile-float-bar-overlay .float-btn {{
                    color: #888;
                    display: flex; flex-direction: column; align-items: center; justify-content: center;
                    cursor: pointer; transition: all 0.2s ease;
                    user-select: none; width: 33%; height: 100%;
                }}
                #my-mobile-float-bar-overlay .float-btn .icon {{
                    font-size: 24px; margin-bottom: 0; /* Larger icon, no bottom margin */
                    transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }}
                #my-mobile-float-bar-overlay .float-btn .label {{
                    display: none; /* Hide labels */
                }}
                #my-mobile-float-bar-overlay .float-btn.active {{
                    color: #56CCF2; /* Theme Blue */
                }}
                #my-mobile-float-bar-overlay .float-btn.active .icon {{
                    transform: scale(1.15); /* Scale instead of translateY */
                    filter: drop-shadow(0px 2px 4px rgba(86,204,242,0.4));
                }}
                #my-mobile-float-bar-overlay .float-btn:active .icon {{ 
                    transform: scale(0.9); 
                }}
            </style>
            <div class="mobile-float-bar">
                <div class="float-btn {is_chat}" onclick="window.mobileNavClick('chat')">
                    <div class="icon">🤖</div>
                    <div class="label">AI助手</div>
                </div>
                <div class="float-btn {is_home}" onclick="window.mobileNavClick('home')">
                    <div class="icon">🏠</div>
                    <div class="label">首页</div>
                </div>
                <div class="float-btn {is_settings}" onclick="window.mobileNavClick('settings')">
                    <div class="icon">⚙️</div>
                    <div class="label">设置</div>
                </div>
            </div>
        `;
        
        // Loop to ensuring hiding works
        setInterval(hideTrigger, 500);
        hideTrigger();
    </script>
    """
    components.html(js_payload, height=0, width=0)

def render_mobile_dashboard(df, services, supabase, user):
    # Ultra-Compact CSS for Mobile
    st.markdown("""
        <style>
            /* Mobile General Cleanup */
            section[data-testid='stSidebar'] {display: none;}
            .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
            
            /* Ultra-Compact Budget Cards */
            .budget-card-container { margin-bottom: 12px !important; box-shadow: none !important; border: 1px solid #333; }
            .bc-top { 
                padding: 10px 16px !important; 
                display: flex !important; 
                flex-direction: row !important;
                align-items: center !important; 
                justify-content: space-between !important; 
            }
            .bc-cat-row { margin-bottom: 0 !important; display: flex; align-items: center; }
            .bc-cat-name { font-size: 1rem !important; margin-right: 8px !important; }
            .bc-icon-box { 
                width: 28px !important; height: 28px !important; 
                font-size: 0.9rem !important; border-radius: 8px !important;
                display: flex !important;
            }
            
            .bc-bottom { padding: 20px 16px 20px 16px !important; background: transparent !important; border-top: none !important;}
            
            /* Hide elements to save space */
            .bc-amount-sub { font-size: 0.75rem !important; opacity: 0.6; }
            .timeline-row { display: none !important; }
            .bc-advice { display: none !important; }
            .marker-today { display: none !important; }
            
            /* Slim Progress Bar (28px - Increased) */
            .track-container { height: 28px !important; margin: 0 !important; background: rgba(255,255,255,0.05); border-radius: 14px; }
            .track-bg { height: 28px !important; border-radius: 14px; background: transparent !important; }
            .track-fill { height: 28px !important; border-radius: 14px; box-shadow: none !important; }
            .track-text-overlay { display: block !important; font-size: 0.8rem !important; line-height: 28px !important; font-weight: 700 !important; } /* Show % */
            
            /* Section Headers */
            h3 { font-size: 1rem !important; margin-bottom: 10px !important; opacity: 0.9; margin-top: 20px !important;}
        </style>
    """, unsafe_allow_html=True)

    # === Mobile Router ===
    if st.session_state.get("v2_page") == "Smart Chat":
        # Floating Bar handles navigation back
        render_chat(df, services, supabase, user, is_mobile=True)
        render_mobile_floating_bar()
        return
    elif st.session_state.get("v2_page") == "Settings":
        render_settings(supabase, user, is_mobile=True)
        render_mobile_floating_bar()
        return

    # === Dashboard Content ===
    # 1. Unified KPI Card
    render_unified_kpi_card(df, services, supabase)
    
    # 2. Category Pie Chart (Analysis)
    st.subheader("📊 分类占比")
    if not df.empty and "分类" in df.columns:
         icon_map = {"餐饮": "🍔", "日用品": "🛒", "交通": "🚗", "服饰": "👔", "医疗": "💊", "娱乐": "🎮", "居住": "🏠", "其他": "📦"}
         df_pie = df.copy()
         df_pie["IconLabel"] = df_pie["分类"].apply(lambda x: f"{icon_map.get(x, '💰')} {x}")
         
         user = st.session_state.get("user")
         user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
         
         fig = px.pie(df_pie, names="IconLabel", values="有效金额", hole=0.6, 
             color_discrete_sequence=["#2F80ED", "#56CCF2", "#6FCF97", "#F2C94C", "#BB6BD9", "#EB5757", "#9B51E0", "#2D9CDB"])
         fig.update_traces(
             textinfo='percent+label', 
             textposition='inside', 
             textfont_color="white",
             hovertemplate="%{label}<br>有效金额: " + user_currency + "%{value:,.2f}<extra></extra>"
         )
         fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, b=0, l=0, r=0), showlegend=False, height=260)
         st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

    # 3. Budget Cards
    st.subheader("💰 预算详情")
    render_budget_cards(df, services, supabase, is_mobile=True)

    # 4. Trend Chart
    st.subheader("📉 支出趋势")
    tz = pytz.timezone("Asia/Shanghai")
    this_month = pd.Timestamp.now(tz=tz).strftime("%Y-%m")
    if "月(yyyy-mm)" in df.columns:
        user = st.session_state.get("user")
        user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
        
        daily_trend = df[df["月(yyyy-mm)"] == this_month].groupby("日期")["有效金额"].sum().reset_index()
        if not daily_trend.empty:
            fig = px.area(daily_trend, x="日期", y="有效金额", title="", color_discrete_sequence=["#56CCF2"])
            fig.update_traces(hovertemplate="%{x}<br>有效金额: " + user_currency + "%{y:,.2f}<extra></extra>")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(showgrid=False, visible=False, title=None), 
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", visible=True, title=None),
                height=150
            )
            st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})
        else:
            st.info("本月暂无数据")
            
    # 5. Heatmap
    with st.container():
        # st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True) # Removed spacer
        render_heatmap(supabase, is_mobile=True)

    # 6. Recent Records
    st.subheader("📝 最近记录")
    if not df.empty:
        df_sorted = df.sort_values(by=["date", "id"], ascending=[False, False]).head(5)
        user = st.session_state.get("user")
        user_currency = user.user_metadata.get("currency_symbol", "$").split(" ")[0] if user else "$"
        
        for _, row in df_sorted.iterrows():
            cat = row["分类"]
            icon_map = {"餐饮": "🍔", "日用品": "🛒", "交通": "🚗", "服饰": "👔", "医疗": "💊", "娱乐": "🎮", "居住": "🏠", "其他": "📦"}
            icon = icon_map.get(cat, "💰")
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 16px; background:#181818; border-radius:12px; margin-bottom:8px; border:1px solid #2A2A2A;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="font-size:1.2rem;">{icon}</div>
                    <div style="font-weight:500; font-size:0.95rem; color:#eee;">{row['项目']}</div>
                </div>
                <div style="font-size:0.95rem; font-weight:600; color:#FF4B4B;">-{user_currency}{row['有效金额']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # 7. Navigation (Floating Bar)
    render_mobile_floating_bar()


# ==========================================
# MAIN RENDER ENTRY
# ==========================================
def render(supabase):
    inject_custom_css()
    
    # Device Detection
    device_type = utils.get_device_type()
    # device_type = "mobile" # Force mobile for testing CSS overrides
    
    if device_type == "mobile":
        # Inject Mobile Specific CSS Overrides to compact the UI
        st.markdown("""
        <style>
            /* Aggressive Mobile Reduction (~2/3 height) */
            .bc-top { padding: 4px 16px !important; }
            .bc-bottom { padding: 8px 16px !important; }
            .track-container { height: 35px !important; margin-bottom: 4px !important; }
            
            /* Smaller Fonts & Icons */
            .bc-icon-box { 
                width: 42px !important; 
                height: 42px !important; 
                font-size: 1.2rem !important; 
                border-radius: 12px !important;
            }
            .bc-cat-name { font-size: 1.1rem !important; }
            .bc-amount-big { font-size: 1.4rem !important; }
            .bc-amount-sub { font-size: 0.75rem !important; }
            .timeline-row { margin-bottom: 6px !important; font-size: 0.7rem !important; }
            .bc-advice { font-size: 0.7rem !important; margin-top: 8px !important; }
            .budget-card-container { margin-bottom: 8px !important; }
            
            /* Section Headers */
            h2, h3, .kpi-title { font-size: 1.1rem !important; }
        </style>
        """, unsafe_allow_html=True)
        
        # Fallthrough to Desktop Logic but with is_mobile flag passed down
        # Mobile View Entry (Legacy) -> Redirecting to Desktop View
        pass
        
        # New Mobile View Entry
        user = st.session_state.get("user")
        if user:
            df = services.load_expenses(supabase)
            render_mobile_dashboard(df, services, supabase, user)
            return
        
    # Desktop View Entry (Original Logic)
    with st.sidebar:
        logo_url = "https://api.dicebear.com/9.x/bottts/svg?seed=FinanceHelper&backgroundColor=00a6ff"
        
        user = st.session_state.get("user")
        if user and user.user_metadata.get("avatar_url"):
            logo_url = user.user_metadata.get("avatar_url")
        
        st.image(logo_url, width=100)
        st.markdown(f"### 智能记账小助手")
        st.divider()
        page = render_sidebar_nav()
        st.divider()
    
    # Initialize Page variable if not set
    if "v2_page" not in st.session_state:
        st.session_state["v2_page"] = "Dashboard"
    
    page = st.session_state["v2_page"]
    
    df = services.load_expenses(supabase)
    
    if page == "Dashboard":
        render_desktop_dashboard(df, services, supabase, is_mobile=(device_type == "mobile"))
    elif page == "Transactions":
        render_transactions(df, services, supabase, is_mobile=(device_type == "mobile"))
    elif page == "Analysis":
        render_analysis(df, services, supabase, is_mobile=(device_type == "mobile"))
    elif page == "Budgets":
        render_budgets(df, services, supabase, st.session_state["user"], is_mobile=(device_type == "mobile"))
    elif page == "Subscriptions":
        render_subscriptions(df, services, supabase, is_mobile=(device_type == "mobile"))
    elif page == "Settings":
        render_settings(supabase, st.session_state["user"], is_mobile=(device_type == "mobile"))
    elif page == "Smart Chat":
        render_chat(df, services, supabase, st.session_state["user"], is_mobile=(device_type == "mobile"))
