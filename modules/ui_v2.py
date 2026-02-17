import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import modules.services as services

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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        
        div.block-container {
            padding-top: 4rem;
        }

        /* KPI Button Styling */
        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            height: auto;
            padding: 15px;
            text-align: left;
            border: 1px solid rgba(255,255,255,0.1);
            background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
            transition: transform 0.2s, border-color 0.2s;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            border-color: rgba(255,255,255,0.3);
            background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        }
        div.stButton > button p {
            font-size: 1.1rem;
        }

        /* Sidebar Navigation */
        section[data-testid="stSidebar"] {
            background-color: #0E1117;
            border-right: 1px solid rgba(255,255,255,0.05);
        }

        /* Custom Tabs/Nav */
        .nav-btn {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            margin-bottom: 4px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
            color: #E0E0E0;
            text-decoration: none;
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
        }
        .nav-btn:hover {
            background: rgba(255,255,255,0.05);
        }
        .nav-btn.active {
            background: rgba(46, 134, 193, 0.2);
            color: #56CCF2;
            font-weight: 600;
            border-left: 3px solid #56CCF2;
        }
        
        /* Chat Styling */
        .chat-container {
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            background-color: rgba(14, 17, 23, 0.5);
        }
        
        /* Table / Dataframes */
        thead tr th:first-child { display:none }
        tbody th { display:none }
        
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
    </style>
    """, unsafe_allow_html=True)
    
    # Reverse map for value lookup
    rev_options = {v: k for k, v in NAV_OPTIONS.items()}
    
    # Ensure session state exists
    if "v2_page" not in st.session_state:
        st.session_state["v2_page"] = "Dashboard"
        
    current_val = NAV_OPTIONS.get(st.session_state["v2_page"], NAV_OPTIONS["Dashboard"])
    
    selected_val = st.radio(
        "Menu",
        list(NAV_OPTIONS.values()),
        index=list(NAV_OPTIONS.values()).index(current_val),
        label_visibility="collapsed",
        key="v2_nav_radio"
    )
    
    # Update state if changed
    new_page = rev_options.get(selected_val)
    if new_page != st.session_state["v2_page"]:
        st.session_state["v2_page"] = new_page
        st.rerun()
        
    return st.session_state["v2_page"]

def navigate_to(page_key):
    st.session_state["v2_page"] = page_key
    # Sync radio button if it exists and is valid
    if "v2_nav_radio" in st.session_state and page_key in NAV_OPTIONS:
        st.session_state["v2_nav_radio"] = NAV_OPTIONS[page_key]

def render_top_navigation(df, services, supabase):
    # KPIs
    this_month = pd.Timestamp.today().strftime("%Y-%m")
    
    if "月(yyyy-mm)" in df.columns:
        month_df = df[df["月(yyyy-mm)"] == this_month]
        month_total = month_df["有效金额"].sum()
        count = len(month_df)
    else:
        month_total = 0
        count = 0
        
    # Budget Logic
    budgets = services.get_budgets(supabase)
    budget_total = sum([b["amount"] for b in budgets])
    left = budget_total - month_total
    
    # Recurring
    subs = services.get_recurring_rules(supabase)
    active_subs = len(subs)

    c1, c2, c3 = st.columns(3)
    
    # KPI 1: Expenses -> To Transactions
    with c1:
        st.button(
            f"📅 本月支出 (Expense)\n\n# ${month_total:,.2f}\n\n{count} 笔交易", 
            use_container_width=True,
            help="点击查看详细记录",
            on_click=navigate_to,
            args=("Transactions",)
        )

    # KPI 2: Budget -> To Analysis
    with c2:
        color_ind = "✅" if left >= 0 else "⚠️"
        st.button(
            f"💰 剩余预算 (Budget)\n\n# ${left:,.2f}\n\n{color_ind} 总额: ${budget_total:,.0f}", 
            use_container_width=True,
            help="点击查看分析",
            on_click=navigate_to,
            args=("Analysis",)
        )

    # KPI 3: Subs -> To Subscriptions
    with c3:
        st.button(
            f"🔄 活跃订阅 (Subs)\n\n# {active_subs}\n\n固定支出项目", 
            use_container_width=True,
            help="点击管理订阅",
            on_click=navigate_to,
            args=("Subscriptions",)
        )
    
    st.write("")

def render_dashboard(df, services, supabase):
    render_top_navigation(df, services, supabase)
    st.header("总览")
    
    this_month = pd.Timestamp.today().strftime("%Y-%m")
    
    # Charts Area
    col_chart, col_list = st.columns([2, 1])
    
    with col_chart:
        with st.container(border=True):
            st.subheader("📊 支出趋势")
            if "月(yyyy-mm)" in df.columns:
                daily_trend = df[df["月(yyyy-mm)"] == this_month].groupby("日期")["有效金额"].sum().reset_index()
                if not daily_trend.empty:
                    fig = px.area(daily_trend, x="日期", y="有效金额", title="", color_discrete_sequence=["#56CCF2"])
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        margin=dict(l=0, r=0, t=10, b=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("本月暂无数据")
            else:
                st.info("无数据")

    with col_list:
        with st.container(border=True):
            st.subheader("🕒 最近记录")
            if not df.empty:
                # Simplified list
                recent = df.head(5)[["项目", "金额", "日期"]]
                for i, row in recent.iterrows():
                    d = pd.to_datetime(row["日期"]).strftime("%m-%d")
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                        <div>
                            <span style="color:#eee; font-weight:500;">{row['项目']}</span><br>
                            <span style="color:#888; font-size:12px;">{d}</span>
                        </div>
                        <div style="color:#56CCF2; font-weight:600;">${row['金额']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("无最近记录")
                
def render_analysis(df, services, supabase):
    render_top_navigation(df, services, supabase)
    st.header("深度分析")
    
    # === Budget Progress Section (Visuals & Link to Management) ===
    with st.container(border=True):
        c_title, c_link = st.columns([3, 1])
        with c_title:
            st.subheader("📊 预算详情 (Budget Breakdown)")
        with c_link:
            st.button(
                "⚙️ 管理预算", 
                key="goto_budget_manage", 
                use_container_width=True,
                on_click=navigate_to,
                args=("Budgets",)
            )
        
        budgets = services.get_budgets(supabase)
        this_month = pd.Timestamp.today().strftime("%Y-%m")
        
        if budgets:
            # Prepare data
            df_budget_calc = df.copy()
            if "月(yyyy-mm)" in df_budget_calc.columns:
                df_budget_calc = df_budget_calc[df_budget_calc["月(yyyy-mm)"] == this_month]
            
            # Grid layout for budgets
            cols = st.columns(2) 
            for i, b in enumerate(budgets):
                with cols[i % 2]:
                    spent = df_budget_calc[df_budget_calc["分类"] == b["category"]]["有效金额"].sum() if "分类" in df_budget_calc.columns else 0
                    limit = b["amount"]
                    
                    pct = spent / limit if limit > 0 else 0
                    pct_clamped = min(pct, 1.0) * 100
                    
                    if pct > 1.0: color = "#FF416C" # Red
                    elif pct > 0.8: color = "#F2994A" # Orange
                    elif pct > 0.5: color = "#FFD700" # Yellow
                    else: color = "#2F80ED" # Blue
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 15px; padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px; align-items:center;">
                            <span style="font-weight:600; color:#eee; font-size:1.1em;">{b['category']}</span>
                            <span style="font-size:0.9em; color:{color};">${spent:,.0f} / ${limit:,.0f}</span>
                        </div>
                        <div style="width:100%; background:rgba(255,255,255,0.1); border-radius:8px; height:18px;">
                            <div style="width:{pct_clamped}%; background:{color}; height:100%; border-radius:8px; transition: width 0.5s; box-shadow: 0 0 10px {color}66;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("暂无预算配置 (No Budgets Set)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("分类占比 (Category)")
        if not df.empty and "分类" in df.columns:
             fig = px.pie(df, names="分类", values="有效金额", hole=0.6, color_discrete_sequence=px.colors.sequential.Blues_r)
             fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
             st.plotly_chart(fig, use_container_width=True)
             
    with c2:
        st.subheader("月度对比 (Monthly)")
        if not df.empty and "月(yyyy-mm)" in df.columns:
            monthly = df.groupby("月(yyyy-mm)")["有效金额"].sum().reset_index()
            fig = px.bar(monthly, x="月(yyyy-mm)", y="有效金额", text_auto=".2s")
            fig.update_traces(marker_color='#2F80ED', marker_line_width=0)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
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
            
            r_date = st.date_input("首次/下次扣款日期", value=pd.Timestamp.today())
            
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
        this_month = pd.Timestamp.today().strftime("%Y-%m")
        
        if budgets:
            # Prepare data
            df_budget_calc = df.copy()
            if "月(yyyy-mm)" in df_budget_calc.columns:
                df_budget_calc = df_budget_calc[df_budget_calc["月(yyyy-mm)"] == this_month]
            
            # Grid layout for budgets
            cols = st.columns(2) 
            for i, b in enumerate(budgets):
                with cols[i % 2]:
                    spent = df_budget_calc[df_budget_calc["分类"] == b["category"]]["有效金额"].sum() if "分类" in df_budget_calc.columns else 0
                    limit = b["amount"]
                    
                    pct = spent / limit if limit > 0 else 0
                    pct_clamped = min(pct, 1.0) * 100
                    
                    if pct > 1.0: color = "#FF416C" # Red
                    elif pct > 0.8: color = "#F2994A" # Orange
                    elif pct > 0.5: color = "#FFD700" # Yellow
                    else: color = "#2F80ED" # Blue
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 15px; padding: 15px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px; align-items:center;">
                            <span style="font-weight:600; color:#eee; font-size:1.1em;">{b['category']}</span>
                            <span style="font-size:0.9em; color:{color};">${spent:,.0f} / ${limit:,.0f}</span>
                        </div>
                        <div style="width:100%; background:rgba(255,255,255,0.1); border-radius:8px; height:18px;">
                            <div style="width:{pct_clamped}%; background:{color}; height:100%; border-radius:8px; transition: width 0.5s; box-shadow: 0 0 10px {color}66;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("暂无预算配置 (No Budgets Set)")
    
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
def render(supabase):
    inject_custom_css()
    
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
        render_dashboard(df, services, supabase)
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
