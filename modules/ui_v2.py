import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import datetime
import pytz
import modules.services as services
import modules.utils as utils

# Optional imports
try:
    import expense_chat
except ImportError:
    pass

CATEGORIES = ["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "居住", "其他"]

# ==========================================
# CUSTOM CSS & COMPONENTS
# ==========================================
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
    "Smart Chat": "💬  助手 (AI Chat)"
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

def render_budget_cards(df, services, supabase):
    budgets = services.get_budgets(supabase)
    tz = pytz.timezone("Asia/Shanghai")
    now = pd.Timestamp.now(tz=tz)
    this_month_str = now.strftime("%Y-%m")
    
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
                    advice_text = f"建议每日消费 <span style='color:#fff; font-weight:600;'>${daily_budget:.0f}</span>，还剩 {days_left} 天"
                elif left <= 0:
                    advice_text = "⚠️ 预算已超支 (Over Budget)"
                else: # Last day
                    advice_text = f"最后一天，剩余预算 ${left:.0f}"

                # Health & Gradient Determination
                # Logic: Compare Spending Pct vs Time Pct
                # If Spending > Time + 10% -> Red (Danger)
                # If Spending > Time -> Orange (Warning)
                # Else -> Blue/Teal (Healthy)
                
                if pct > 1.0:
                    grad_class = "grad-red" # Over limit
                    text_color = "#ffcccc"
                elif pct * 100 > time_pct + 10:
                    grad_class = "grad-orange" # Spending faster than time
                    text_color = "#ffeebb"
                else:
                    grad_class = "grad-teal" # Healthy
                    text_color = "#d1f7ff"
                
                icon = icon_map.get(b["category"], "💰")
                
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
                        padding: 24px;
                        color: white;
                        position: relative;
                    }}
                    .grad-teal {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
                    .grad-orange {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
                    .grad-red {{ background: linear-gradient(135deg, #ff0844 0%, #ffb199 100%); }}
                    
                    .bc-cat-row {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }}
                    .bc-cat-name {{ font-size: 1.4rem; font-weight: 700; opacity: 0.95; }}
                    .bc-icon-box {{ 
                        background: rgba(255,255,255,0.2); 
                        width: 40px; height: 40px; border-radius: 12px; 
                        display: flex; align-items: center; justify-content: center; 
                        backdrop-filter: blur(4px);
                    }}
                    .bc-amount-big {{ font-size: 1.8rem; font-weight: 800; line-height: 1.1; }}
                    .bc-amount-sub {{ font-size: 0.9rem; opacity: 0.8; font-weight: 500; }}
                    
                    .bc-bottom {{
                        background: #181818;
                        padding: 20px 24px;
                        border-top: 1px solid rgba(255,255,255,0.05);
                    }}
                    .timeline-row {{
                        display: flex; justify-content: space-between;
                        color: #666; font-size: 0.75rem; font-weight: 600;
                        align-items: center;
                        margin-bottom: 12px;
                    }}
                    .track-container {{
                        position: relative;
                        height: 36px; /* Space for marker */
                        margin-bottom: 8px;
                    }}
                    .track-bg {{
                        position: absolute; top: 18px; left: 0; right: 0;
                        height: 6px; background: #333; border-radius: 3px;
                    }}
                    .track-fill {{
                        position: absolute; top: 18px; left: 0;
                        height: 6px; background: rgba(255,255,255,0.9); border-radius: 3px;
                        width: {pct_clamped}%;
                        box-shadow: 0 0 8px rgba(255,255,255,0.5);
                        transition: width 0.5s ease;
                    }}
                    .marker-today {{
                        position: absolute; top: 0; left: {time_pct}%;
                        transform: translateX(-50%);
                        display: flex; flex-direction: column; align-items: center;
                    }}
                    .marker-bubble {{
                        background: #fff; color: #000;
                        padding: 2px 6px; border-radius: 6px;
                        font-size: 0.7rem; font-weight: 700;
                        margin-bottom: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }}
                    .marker-line {{
                        width: 2px; height: 16px; background: #fff; opacity: 0.5;
                    }}
                    
                    .bc-advice {{
                        text-align: center; color: #888; font-size: 0.8rem; margin-top: 8px;
                    }}
                </style>
                
                <div class="budget-card-container">
                    <div class="bc-top {grad_class}">
                        <div class="bc-cat-row">
                            <div class="bc-cat-name">{b['category']}</div>
                            <div class="bc-icon-box" style="font-size: 1.2rem;">{icon}</div>
                        </div>
                        <div class="bc-amount-big">${left:,.0f}</div>
                        <div class="bc-amount-sub">left of ${limit:,.0f}</div>
                    </div>
                    <div class="bc-bottom">
                        <div class="timeline-row">
                            <span>{start_str}</span>
                            <span style="font-size: 1rem; color: #eee; font-weight: 700;">{int(pct_clamped)}%</span>
                            <span>{end_str}</span>
                        </div>
                        <div class="track-container">
                            <div class="track-bg"></div>
                            <div class="track-fill"></div>
                            <div class="marker-today">
                                <div class="marker-bubble">Today</div>
                                <div class="marker-line"></div>
                            </div>
                        </div>
                        <div class="bc-advice">
                            {advice_text}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("暂无预算配置 (No Budgets Set)")

def render_top_navigation(df, services, supabase):
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
    left = budget_total - month_total
    
    subs = services.get_recurring_rules(supabase)
    active_subs = len(subs)

    # Render Clickable KPI Cards with Ghost Button Strategy (Overlay)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div id="kpi-card-1" class="kpi-card-visual kpi-blue">
            <div class="kpi-title">📅 本月支出 (Month)</div>
            <div class="kpi-value">${month_total:,.2f}</div>
            <div class="kpi-meta">{count} 笔交易</div>
        </div>
        """, unsafe_allow_html=True)
        st.button(" ", key="btn_trans_ghost", use_container_width=True, on_click=navigate_to, args=("Transactions",))

    with c2:
        st.markdown(f"""
        <div id="kpi-card-2" class="kpi-card-visual kpi-purple">
            <div class="kpi-title">💰 剩余预算 (Left)</div>
            <div class="kpi-value">${left:,.2f}</div>
            <div class="kpi-meta">总额: ${budget_total:,.0f}</div>
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

def render_heatmap(supabase):
    # Load data for 6 months (~182 days)
    data = services.get_daily_activity(supabase, days=200) 
    if not data: return
    
    tz = pytz.timezone("Asia/Shanghai")
    today = datetime.datetime.now(tz).date()
    days_to_show = 182 # 26 weeks * 7 = 182 days
    start_date = today - datetime.timedelta(days=days_to_show - 1)
    
    cells = []
    months = []
    last_month = ""
    
    for i in range(days_to_show):
        d = start_date + datetime.timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        count = data.get(d_str, 0)
        
        # Color scale
        if count == 0: color = "#2d333b"
        elif count <= 2: color = "#0e4429"
        elif count <= 5: color = "#006d32"
        elif count <= 10: color = "#26a641"
        else: color = "#39d353"
        
        cells.append(f'<div class="heatmap-cell" style="background-color:{color};" title="{d_str}: {count}"></div>')
        
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
            height: 280px; /* Force height to match Trend Card (280px requested) */
            justify-content: space-between;
        }}
        .heatmap-inner-wrapper {{
            width: 100%;
            overflow-x: auto;
            margin-top: 10px;
        }}
        .heatmap-grid {{
            display: grid;
            grid-template-rows: repeat(7, 20px); /* 20px cells */
            grid-auto-flow: column;
            gap: 3px;
            margin-bottom: 8px;
        }}
        .heatmap-cell {{
            width: 20px;
            height: 20px;
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
        <div class="kpi-title" style="margin-bottom:15px;">🔥 活跃分布 (Activity)</div>
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

def render_desktop_dashboard(df, services, supabase):
    render_top_navigation(df, services, supabase)
    
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
            
            if "月(yyyy-mm)" in df.columns:
                daily_trend = df[df["月(yyyy-mm)"] == this_month].groupby("日期")["有效金额"].sum().reset_index()
                if not daily_trend.empty:
                    fig = px.area(daily_trend, x="日期", y="有效金额", title="", color_discrete_sequence=["#56CCF2"])
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(showgrid=False, tickfont=dict(color="#888")),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#888")),
                        height=230 # Reduced to 230 to match Heatmap 270px total
                    )
                    st.plotly_chart(fig, use_container_width=True)
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
                <div style="color:#FF4B4B; font-weight:600;">-${row['有效金额']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.caption("无最近记录")
                
def render_analysis(df, services, supabase):
    render_top_navigation(df, services, supabase)
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
             
             fig = px.pie(df_pie, names="IconLabel", values="有效金额", hole=0.6, 
                 color_discrete_sequence=["#2F80ED", "#56CCF2", "#6FCF97", "#F2C94C", "#BB6BD9", "#EB5757", "#9B51E0", "#2D9CDB"])
             fig.update_traces(textinfo='percent+label', textposition='inside', textfont_color="white")
             fig.update_layout(
                 paper_bgcolor="rgba(0,0,0,0)", 
                 margin=dict(t=20, b=20, l=20, r=20), 
                 showlegend=False
             )
             st.plotly_chart(fig, use_container_width=True)
             
    with c2:
        st.subheader("月度对比 (Monthly)")
        if not df.empty and "月(yyyy-mm)" in df.columns:
            monthly = df.groupby("月(yyyy-mm)")["有效金额"].sum().reset_index()
            fig = px.bar(monthly, x="月(yyyy-mm)", y="有效金额", text_auto=".2s")
            fig.update_traces(marker_color='#2F80ED', marker_line_width=0, textfont_color="#fff")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#888")),
                xaxis=dict(tickfont=dict(color="#888"))
            )
            st.plotly_chart(fig, use_container_width=True)

def render_subscriptions(df, services, supabase):
    render_top_navigation(df, services, supabase)
    st.header("订阅管理 (Subscriptions)")
    
    rules = services.get_recurring_rules(supabase)
    if not rules:
        st.info("暂无订阅信息，请点击右上角 '+' 按钮添加。")
        rules = []

    # 1. Summary Cards
    total_monthly = sum([r["amount"] for r in rules if r["frequency"] == "Monthly"]) + \
                    sum([r["amount"] * 4 for r in rules if r["frequency"] == "Weekly"]) + \
                    sum([r["amount"] / 12 for r in rules if r["frequency"] == "Yearly"])
                    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("月度固定支出 (Est. Monthly)", f"${total_monthly:,.2f}")
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
            r_amt = c_amt.number_input("金额 ($)", min_value=0.0, step=1.0)
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
            "amount": st.column_config.NumberColumn("金额", format="$%.2f", width="small"),
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

def render_transactions(df, services, supabase):
    render_top_navigation(df, services, supabase)
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
    
    col_cfg = {
        "删除": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
        "日期": st.column_config.DateColumn("日期", width="medium"),
        "项目": st.column_config.TextColumn("项目", width="large"),
        "金额": st.column_config.NumberColumn("金额 ($)", format="$%.2f", width="small"),
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

def render_chat(df, services, supabase, user):
    render_top_navigation(df, services, supabase)
    st.header("AI 智能助手")
    st.caption("告诉我你花了什么钱，或者问我财务问题。")

    chat_container = st.container(height=500, border=True)
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 准备好记账了吗？"}]
        
    with chat_container:
        for msg in st.session_state.messages:
             role = msg["role"]
             avatar = "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput" if role == "assistant" else "https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123"
             st.chat_message(role, avatar=avatar).write(msg["content"])

    if prompt := st.chat_input("例如：打车 50，超市买菜 120..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user", avatar="https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123").write(prompt)
        
        with chat_container:
             with st.chat_message("assistant", avatar="https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput"):
                 ph = st.empty()
                 ph.write("Thinking...")
                 
                 result = expense_chat.process_user_message(prompt, df)
                 reply = "Completed."
                 
                 intent = result.get("type", "chat")
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
                 elif intent == "chat":
                     reply = result.get("reply", "...")
                 
                 ph.write(reply)
                 st.session_state.messages.append({"role": "assistant", "content": reply})
                 
    if st.session_state.get("data_changed"):
        st.cache_data.clear()
        del st.session_state["data_changed"]
        st.rerun()

    st.divider()
    with st.expander("⚙️ 设置 & 账号 (Settings)", expanded=False):
        st.write(f"Email: {user.email}")
        
        st.divider()
        st.write("🎨 个性化 (Customization)")
        uploaded_logo = st.file_uploader("更换 Logo (Change Logo)", type=["png", "jpg", "jpeg"], key="v2_logo_uploader")
        if uploaded_logo:
             import os
             if not os.path.exists("assets"): os.makedirs("assets")
             with open("assets/logo.png", "wb") as f:
                 f.write(uploaded_logo.getbuffer())
             st.success("✅ Logo 已更新! (Updated)")
             time.sleep(1)
             st.rerun()
             
        st.divider()
        if st.button("注销 (Logout)", type="secondary", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state["session"] = None
            st.rerun()

def render_budgets(df, services, supabase, user):
    render_top_navigation(df, services, supabase)
    st.header("预算管理 (Budgets)")
    
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
            b_amt = st.number_input("限额 ($)", min_value=0, step=100, key="v2_b_amt_page")
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
            "amount": st.column_config.NumberColumn("限额", min_value=0, step=100, format="$%d"),
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



# ==========================================
# MAIN RENDER ENTRY
# ==========================================
def render_mobile_dashboard(df, services, supabase, user):
    # Mobile Specific Dashboard
    # 1. Hide Sidebar
    st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    st.markdown(f"### 📱 早上好, {user.email.split('@')[0]}")
    
    # 2. Big Cards (Vertical)
    render_budget_cards(df, services, supabase)
    
    # 3. Recent Transactions (Simple List)
    st.subheader("📝 最近流水")
    if not df.empty:
        df_sorted = df.sort_values(by=["date", "id"], ascending=[False, False]).head(5)
        for _, row in df_sorted.iterrows():
            cat = row["分类"]
            icon_map = {"餐饮": "🍔", "日用品": "🛒", "交通": "🚗", "服饰": "👔", "医疗": "💊", "娱乐": "🎮", "居住": "🏠", "其他": "📦"}
            icon = icon_map.get(cat, "💰")
            
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:15px; background:#1E1E1E; border-radius:12px; margin-bottom:10px; border:1px solid #333;">
                <div style="display:flex; align-items:center; gap:15px;">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div>
                        <div style="font-weight:600; font-size:1rem; color:#eee;">{row['项目']}</div>
                        <div style="font-size:0.8rem; color:#888;">{pd.to_datetime(row['日期']).strftime('%m-%d')} • {cat}</div>
                    </div>
                </div>
                <div style="font-size:1.1rem; font-weight:700; color:#FF4B4B;">-${row['有效金额']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # 4. Mobile Bottom Nav (Simulated via columns at bottom)
    st.divider()
    c1, c2, c3 = st.columns(3)
    if c1.button("🏠 首页", key="mob_nav_home", use_container_width=True):
        st.session_state["v2_page"] = "Dashboard"
        st.rerun()
    if c2.button("➕ 记一笔", key="mob_nav_add", use_container_width=True):
         # Could open a dialog or switch to add page
         with st.popover("记账", use_container_width=True):
             st.write("快速记账")
             # Simple form
             with st.form("mob_quick_add"):
                 item = st.text_input("项目")
                 amt = st.number_input("金额", min_value=0.0)
                 cat = st.selectbox("分类", CATEGORIES)
                 if st.form_submit_button("提交"):
                     services.add_expense(supabase, st.session_state["user"].id, pd.Timestamp.now(), item, amt, cat, "", "mobile")
                     st.success("已记录")
                     time.sleep(1)
                     st.rerun()
                     
    if c3.button("🤖 助手", key="mob_nav_chat", use_container_width=True):
        st.session_state["v2_page"] = "Smart Chat"
        st.rerun()

    # Handle Chat Page in Mobile separately if needed, but for now reuse simple
    if st.session_state["v2_page"] == "Smart Chat":
        render_chat(df, services, supabase, user)


# ==========================================
# MAIN RENDER ENTRY
# ==========================================
def render(supabase):
    inject_custom_css()
    
    # Device Detection
    device_type = utils.get_device_type()
    
    if device_type == "mobile":
        # Mobile View Entry
        user = st.session_state.get("user")
        if not user:
            st.error("请先登录")
            return
            
        df = services.load_expenses(supabase)
        render_mobile_dashboard(df, services, supabase, user)
        return

    # Desktop View Entry (Original Logic)
    with st.sidebar:
        logo_url = "https://api.dicebear.com/9.x/bottts/svg?seed=FinanceHelper&backgroundColor=00a6ff"
        import os
        if os.path.exists("assets/logo.png"):
            logo_url = "assets/logo.png"
        
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
        render_desktop_dashboard(df, services, supabase)
    elif page == "Transactions":
        render_transactions(df, services, supabase)
    elif page == "Analysis":
        render_analysis(df, services, supabase)
    elif page == "Budgets":
        render_budgets(df, services, supabase, st.session_state["user"])
    elif page == "Subscriptions":
        render_subscriptions(df, services, supabase)
    elif page == "Smart Chat":
        render_chat(df, services, supabase, st.session_state["user"])
