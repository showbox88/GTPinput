import time
import pandas as pd
import streamlit as st
import plotly.express as px

import requests
import json
import os
import tempfile
import expense_chat
# Using Try-Except for optional modules to prevent crash if setup isn't perfect yet
try:
    from modules.ai_factory import AIProcessor
    from modules.google_service import GoogleService
    from config.rules import FOLDER_MAP, generate_filename
except ImportError:
    pass

# ====== 配置 (从 secrets 读取) ======
# 需要在 .streamlit/secrets.toml 中配置 API_URL 和 API_KEY
API_URL = st.secrets["general"]["API_URL"]
API_KEY = st.secrets["general"]["API_KEY"]

# ====== Constants ======
CATEGORIES = ["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "居住", "其他"]
# Initialize df globally to prevent NameError if load_data fails or scoping issues occur
df = pd.DataFrame()



# ====== 数据读取 ======
@st.cache_data(ttl=30)  # 30秒缓存
def load_data() -> pd.DataFrame:
    try:
        url = f"{API_URL}/list"
        headers = {"X-API-Key": API_KEY}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 假设数据在 "rows" 字段中，如果直接是列表则直接用
        rows = data.get("rows", []) if isinstance(data, dict) else data
        
        if not rows:
            return pd.DataFrame()
            
        df = pd.DataFrame(rows)
        
        # ====== 字段映射与清洗 ======
        # API返回: id, date, item, amount, category, note, source, created_at
        # 目标列: 月(yyyy-mm), 分类, 有效金额, 创建时间
        
        # 1. 金额处理
        if "amount" in df.columns:
            df["有效金额"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        
        # 2. 日期处理
        if "date" in df.columns:
            df["日期"] = pd.to_datetime(df["date"], errors="coerce")
            df["月(yyyy-mm)"] = df["日期"].dt.strftime("%Y-%m")
            df["年"] = df["日期"].dt.year
            
        # 3. 分类
        if "category" in df.columns:
            df["分类"] = df["category"]
            
        # 4. 创建时间
        if "created_at" in df.columns:
            df["创建时间"] = pd.to_datetime(df["created_at"], errors="coerce")
            
        # 5. 其他展示字段映射
        df["项目"] = df.get("item", "")
        df["备注"] = df.get("note", "")
        df["金额"] = df.get("amount", 0)  # 显示用的原始金额
        df["来源"] = df.get("source", "")

        return df
        
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

# ====== Helper Functions for V3.0 ======
def get_budgets():
    try:
        resp = requests.get(f"{API_URL}/budget/list", headers={"X-API-Key": API_KEY}, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("rows", [])
    except:
        pass
    return []

def add_budget(name, category, amount, color, icon):
    try:
        payload = {"name": name, "category": category, "amount": float(amount), "color": color, "icon": icon}
        requests.post(f"{API_URL}/budget/add", json=payload, headers={"X-API-Key": API_KEY})
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"添加失败: {e}")
        return False

def delete_budget(bid):
    try:
        requests.post(f"{API_URL}/budget/delete", json={"id": int(bid)}, headers={"X-API-Key": API_KEY})
        st.cache_data.clear()
        return True
    except:
        return False

def get_recurring_rules():
    try:
        resp = requests.get(f"{API_URL}/recurring/list", headers={"X-API-Key": API_KEY}, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("rows", [])
    except:
        pass
    return []

def add_recurring(name, amount, category, frequency, day):
    try:
        payload = {"name": name, "amount": float(amount), "category": category, "frequency": frequency, "day": int(day)}
        requests.post(f"{API_URL}/recurring/add", json=payload, headers={"X-API-Key": API_KEY})
        return True
    except Exception as e:
        st.error(f"添加失败: {e}")
        return False

def delete_recurring(rid):
    try:
        requests.post(f"{API_URL}/recurring/delete", json={"id": int(rid)}, headers={"X-API-Key": API_KEY})
        return True
    except:
        return False

# ==========================================
# Main App Layout with Tabs
# ==========================================

# ====== DATA LOADING ======
# Load data EARLIER so that Chat Logic (in Tab 0) can use it for context!
df = load_data()

tab_chat, tab_dash, tab_settings = st.tabs(["💬 智能输入 (Smart Input)", "📊 仪表盘 (Dashboard)", "⚙️ 管理与设置 (Settings)"])

# ==========================
# TAB 0: SMART INPUT (CHAT)
# ==========================
with tab_chat:
    st.header("💡 智能助手 (Expense & Docs)")
    st.caption("您可以直接输入消费记录（如: 午饭20元），或者上传单据/证件进行归档。")
    
    # --- 1. File Uploader (SmartDoc) ---
    with st.expander("📎 上传文档/证件/单据 (Archive Document)", expanded=False):
        uploaded_file = st.file_uploader("选择文件 (PDF/Image)", type=["png", "jpg", "jpeg", "webp", "pdf"])
        if uploaded_file:
            if st.button("🚀 开始分析与归档"):
                with st.status("正在处理...", expanded=True) as status:
                    # Save to temp
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}")
                    tfile.write(uploaded_file.read())
                    tfile.close()
                    temp_path = tfile.name
                    
                    status.write("🤖 正在调用 AI 进行识别...")
                    try:
                        ai = AIProcessor()
                        res = ai.analyze_image(temp_path)
                        
                        if res.get("type") == "ERROR":
                            st.error(f"识别失败: {res.get('name')}")
                        else:
                            st.success("识别成功！")
                            st.json(res)
                            
                            status.write("📂 正在归档到 Google Drive...")
                            # Prepare data for upload
                            save_data = res.copy()
                            save_data['original_filename'] = uploaded_file.name
                            save_data['temp_path'] = temp_path
                            save_data['extension'] = uploaded_file.name.split('.')[-1]
                            save_data['name'] = res.get('name', 'Unknown')
                            
                            # Upload
                            gs = GoogleService()
                            # Guess folder name mapping from type
                            folder_hint = FOLDER_MAP.get(res.get('type'), FOLDER_MAP["OTHER"])
                            
                            # Generate Name
                            new_name = generate_filename(save_data)
                            
                            link = gs.upload_file(temp_path, new_name, folder_hint)
                            status.write(f"✅ 已上传: {link}")
                            
                            # Sheet & Calendar
                            status.write("📊 更新 Google Sheet & Calendar...")
                            sheet_row = [
                                str(pd.Timestamp.today().date()),
                                save_data.get('name'),
                                save_data.get('type'),
                                save_data.get('doc_id'),
                                save_data.get('expiry_date'),
                                "N/A", # reminder days not asked in simplified flow yet
                                "Skipped",
                                link
                            ]
                            gs.append_to_sheet(sheet_row)
                            
                            # --- NEW: Sync to Expense DB ---
                            try:
                                extract_amt = save_data.get('amount', 0)
                                if isinstance(extract_amt, (int, float)) and extract_amt > 0:
                                    status.write(f"💰 同步记账中 (${extract_amt})...")
                                    # Synthetic Text: "Name Amount Category Note Source:SmartDoc"
                                    # Note: category from SmartDoc might be English (e.g. Food), maybe map it or let backend handle '其他'
                                    s_item = save_data.get('name', 'SmartDoc Item')
                                    s_cat = save_data.get('category', '其他')
                                    s_date = pd.Timestamp.today().strftime("%Y-%m-%d") # or extract date from doc?
                                    
                                    syn_text = f"{s_item} {extract_amt} {s_cat} SmartDoc-Auto-Sync Date:{s_date}"
                                    
                                    requests.post(f"{API_URL}/add", json={"text": syn_text, "source": "smart_doc_upload"}, headers={"X-API-Key": API_KEY})
                                    st.success(f"💰 已同步至账本: {s_item} ${extract_amt}")
                                    st.session_state["data_changed"] = True
                            except Exception as e_sync:
                                print(f"Sync error: {e_sync}")
                                status.write(f"⚠️ 记账同步部分失败: {e_sync}")
                            
                            if save_data.get('expiry_date') != "N/A":
                                gs.add_calendar_reminder(f"{save_data['name']} {save_data['type']}", save_data['expiry_date'], 7) # Default 7 days reminder
                                
                            status.update(label="🎉 归档完成！", state="complete", expanded=False)
                            st.balloons()
                            
                    except Exception as e:
                        st.error(f"处理出错: {e}")
                    
                    # Cleanup? OS remove handled in upload_file or manual?
                    # Python tempfile might need manual removal if delete=False
                    try:
                        os.remove(temp_path)
                    except:
                        pass

    st.divider()

    # --- 2. Chat Interface (Expenses) ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "你好！我是你的记账助手。请告诉我花了什么钱？"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("输入消费 (例如: 打车 50)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Process
        with st.spinner("思考中..."):
            # Pass the FULL dataframe to the chat engine so it can query/delete
            result = expense_chat.process_user_message(prompt, df)
            
            intent_type = result.get("type", "chat")
            
            # 1. Handle Chat/Query Reply
            if "reply" in result:
                ai_reply = result["reply"]
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                st.chat_message("assistant").write(ai_reply)
            
            # 2. Handle Record Intent
            if intent_type == "record":
                exp = result
                # Note: 'item' might be in result directly
                item_str = exp.get('item', 'Unknown')
                amt_str = str(exp.get('amount', 0))
                
                try:
                    # Construct synthetic text for backend
                    date_str = exp.get('date', pd.Timestamp.today().strftime("%Y-%m-%d"))
                    cat_str = exp.get('category', '其他')
                    note_str = exp.get('note', '')
                    synthetic_text = f"{item_str} {amt_str} {cat_str} {note_str} Date:{date_str}"
                    
                    payload = {"text": synthetic_text, "source": "chat_ui"}
                    resp = requests.post(f"{API_URL}/add", json=payload, headers={"X-API-Key": API_KEY})
                    
                    if resp.status_code == 200:
                        st.success(f"✅ 已记录: {item_str} ${amt_str}")
                        st.session_state["data_changed"] = True 
                    else:
                        st.error(f"记录失败: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

            # 3. Handle Delete Intent
            elif intent_type == "delete":
                del_id = result.get("id")
                if del_id:
                    try:
                        resp = requests.post(f"{API_URL}/delete", json={"id": int(del_id)}, headers={"X-API-Key": API_KEY})
                        if resp.status_code == 200:
                             st.success(f"🗑️ 已删除记录 ID: {del_id}")
                             st.session_state["data_changed"] = True
                        else:
                             st.error(f"删除失败: {resp.text}")
                    except Exception as e:
                        st.error(f"Error deleting: {e}")

    if st.session_state.get("data_changed"):
        st.cache_data.clear()
        del st.session_state["data_changed"]
        # Trigger minimal rerun?
        time.sleep(1)
        st.rerun()


# ====== DATA LOADING ======
# Already loaded above.
# df = load_data()

# ====== SIDEBAR FILTERS (Shared effect) ======
st.sidebar.header("筛选 (Filter)")
months = sorted(df["月(yyyy-mm)"].dropna().unique().tolist()) if "月(yyyy-mm)" in df.columns else []
sel_month = st.sidebar.selectbox("月份", options=["全部"] + months, index=(len(months) if months else 0))

sel_categories = None
if "分类" in df.columns:
    cats = sorted(df["分类"].dropna().unique().tolist())
    sel_categories = st.sidebar.multiselect("分类", options=cats, default=[])

# Apply Filter
df_view = df.copy()
is_current_month = False # Flag for budget calc

# If "All" is selected, we can't really calculate monthly budget progress accurately unless we pick 'this month' implicitly?
# Budget logic: Usually compares CURRENT MONTH spending vs Budget.
# If user selects a specific month, we show budget progress for THAT month.
# If user selects "All", maybe we default to Current Month for the Progress Bars? Or hide them?
# Let's align Budget Progress with "Selected Month". If "All", we show "Current Month" progress.

target_month_for_budget = pd.Timestamp.today().strftime("%Y-%m")
if sel_month != "全部":
    df_view = df_view[df_view["月(yyyy-mm)"] == sel_month] if "月(yyyy-mm)" in df_view.columns else df_view
    target_month_for_budget = sel_month

if sel_categories:
    df_view = df_view[df_view["分类"].isin(sel_categories)]


# ==========================
# TAB 1: DASHBOARD
# ==========================
with tab_dash:
    # --- KPI ---
    k1, k2, k3, k4 = st.columns(4)
    
    this_month = pd.Timestamp.today().strftime("%Y-%m")
    this_year = pd.Timestamp.today().year
    
    # Safe Sum Helper
    def safe_sum(dataframe, col):
        return dataframe[col].sum() if col in dataframe.columns else 0

    month_total = df[df["月(yyyy-mm)"] == this_month]["有效金额"].sum() if "月(yyyy-mm)" in df.columns and "有效金额" in df.columns else 0
    year_total = df[df["年"] == this_year]["有效金额"].sum() if "年" in df.columns and "有效金额" in df.columns else 0
    view_total = safe_sum(df_view, "有效金额")
    
    k1.metric("📅 本月支出", f"${month_total:,.2f}")
    k2.metric("🗓️ 今年支出", f"${year_total:,.2f}")
    k3.metric("🔍 当前筛选合计", f"${view_total:,.2f}")
    k4.metric("📝 记录笔数", f"{len(df_view)}")
    
    st.divider()

    # --- BUDGET PROGRESS (New) ---
    st.subheader(f"📊 预算进度 ({target_month_for_budget})")
    budgets = get_budgets()
    
    if not budgets:
        st.info("暂无预算计划，请去“管理与设置”中添加。")
    else:
        # Calculate spending for the target month per category
        # getting full data for calculation to avoid filter interference (except month)
        df_budget_calc = df.copy()
        if "月(yyyy-mm)" in df_budget_calc.columns:
            df_budget_calc = df_budget_calc[df_budget_calc["月(yyyy-mm)"] == target_month_for_budget]
        
        # Helper for Custom Progress Bar
        def render_budget_card(name, icon, amount, limit, color):
            pct = (amount / limit) if limit > 0 else 0
            pct_disp = min(pct * 100, 100)
            
            # Color logic: if over budget, turn red-ish, effectively overridden by user color usually, 
            # but let's stick to user color for the bar, maybe showing warning text.
            bar_color = color
            # Dark mode friendly track: semi-transparent white looks good on dark backgrounds
            bg_color = "rgba(255, 255, 255, 0.1)" 
            
            # HTML for custom bar
            # Height: 24px (taller), Radius: 12px
            # Removed explicit text colors causing visibility issues in dark mode
            html = f"""
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-weight: 500;">
                    <span>{icon} {name}</span>
                    <span style="opacity: 0.8;">${amount:,.0f} / ${limit:,.0f}</span>
                </div>
                <div style="background-color: {bg_color}; border-radius: 12px; height: 24px; width: 100%; overflow: hidden;">
                    <div style="background-color: {bar_color}; width: {pct_disp}%; height: 100%; border-radius: 12px; transition: width 0.5s;"></div>
                </div>
                <div style="text-align: right; font-size: 0.8rem; opacity: 0.7; margin-top: 2px;">
                    使用率: {pct:.1%}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
            if pct > 1.0:
               st.caption(f"⚠️ **已超支 {pct-1:.1%}**")

        # Display in columns of 3
        b_cols = st.columns(3)
        for i, b in enumerate(budgets):
            with b_cols[i % 3]:
                b_cat = b["category"]
                b_limit = b["amount"]
                b_icon = b.get("icon", "💰")
                b_name = b.get("name", b_cat)
                b_color = b.get("color", "#FF4B4B")
                
                # Actual spent in this category for this month
                spent = 0
                if "分类" in df_budget_calc.columns and "有效金额" in df_budget_calc.columns:
                    spent = df_budget_calc[df_budget_calc["分类"] == b_cat]["有效金额"].sum()
                
                render_budget_card(b_name, b_icon, spent, b_limit, b_color)

    st.divider()

    # --- CHARTS ---
    # 移动端适配：st.columns 在手机上会垂直堆叠
    left, right = st.columns([2, 1])

    with left:
        st.subheader("📈 月度趋势")
        if "月(yyyy-mm)" in df.columns and "有效金额" in df.columns:
            month_sum = df.groupby("月(yyyy-mm)", as_index=False)["有效金额"].sum().sort_values("月(yyyy-mm)")
            fig_bar = px.bar(month_sum, x="月(yyyy-mm)", y="有效金额", text_auto=".2s")
            fig_bar.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            fig_bar.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                height=300,
                xaxis_title="",
                yaxis_title="金额 ($)",
                yaxis_tickprefix="$"
            )
            st.plotly_chart(fig_bar, key="chart_bar_1", on_select="ignore") # plotly_chart defaults to using container width in modern streamlit or needs config? 
            # Actually, typically warning implies st.plotly_chart(..., use_container_width=True) -> st.plotly_chart(..., width=None) or similar? 
            # Wait, the warning said: "For `use_container_width=True`, use `width='stretch'`".
            # So:
            st.plotly_chart(fig_bar, width="stretch")
        else:
            st.warning("暂无月度数据")

    with right:
        st.subheader("🥧 分类占比")
        if "分类" in df_view.columns and "有效金额" in df_view.columns:
            cat_sum = df_view.groupby("分类", as_index=False)["有效金额"].sum().sort_values("有效金额", ascending=False)
            if cat_sum.empty:
                st.info("无数据")
            else:
                fig_pie = px.pie(cat_sum, names="分类", values="有效金额", hole=0.4)
                fig_pie.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=300,
                    showlegend=False
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, width="stretch")
        else:
            st.warning("暂无分类数据")

    st.divider()

    # --- RECENT RECORDS (Data Editor) ---
    st.subheader("📄 最近记录")
    if not df_view.empty:
        df_editor = df_view.copy()
        if "id" in df_editor.columns:
            df_editor.set_index("id", inplace=True)
        
        if "删除" not in df_editor.columns:
            df_editor.insert(0, "删除", False)

        show_cols = ["删除", "日期", "项目", "金额", "分类", "备注"]
        final_cols = [c for c in show_cols if c in df_editor.columns]
        
        column_config = {
            "删除": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
            "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD", width="small"),
            "项目": st.column_config.TextColumn("项目", width="medium"),
            "金额": st.column_config.NumberColumn("金额", min_value=0, format="$%.2f", width="small"),
            "分类": st.column_config.SelectboxColumn("分类", options=CATEGORIES, width="small"),
            "备注": st.column_config.TextColumn("备注", width="medium")
        }

        if "创建时间" in df_editor.columns:
            df_editor = df_editor.sort_values("创建时间", ascending=False)

        edited_df = st.data_editor(
            df_editor[final_cols],
            column_config=column_config,
            hide_index=True,
            # width="stretch" replaces use_container_width=True as per deprecation warning
            width="stretch",
            num_rows="fixed",
            key="expense_editor"
        )

        # Logic for Save/Delete buttons (Same as before)
        to_delete_mask = edited_df["删除"] == True
        delete_count = to_delete_mask.sum()
        editor_state = st.session_state.get("expense_editor", {})
        edited_rows_dict = editor_state.get("edited_rows", {})
        has_edits = len(edited_rows_dict) > 0
        
        btn_label = "💾 保存修改"
        btn_type = "primary"
        if delete_count > 0:
            btn_label = f"🗑️ 确认删除 ({delete_count} 条)"
            btn_type = "secondary" 
        
        if st.button(btn_label, type=btn_type, width="stretch"):
            try:
                changes_made = False
                # 1. Delete
                if delete_count > 0:
                    for rec_id, row in edited_df[to_delete_mask].iterrows():
                        requests.post(f"{API_URL}/delete", json={"id": int(rec_id)}, headers={"X-API-Key": API_KEY})
                    st.success(f"已删除 {delete_count} 条")
                    changes_made = True
                
                # 2. Update
                if has_edits:
                    for idx, changes in edited_rows_dict.items():
                        row = edited_df.iloc[idx]
                        if row["删除"]: continue
                        payload = {
                            "id": int(row.name),
                            "date": row["日期"].strftime("%Y-%m-%d") if hasattr(row["日期"], "strftime") else str(row["日期"]),
                            "item": row["项目"],
                            "amount": float(row["金额"]),
                            "category": row["分类"],
                            "note": row["备注"]
                        }
                        requests.post(f"{API_URL}/update", json=payload, headers={"X-API-Key": API_KEY})
                    st.success("已更新修改")
                    changes_made = True

                if changes_made:
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"操作失败: {e}")
    else:
        st.info("暂无数据。")


# ==========================
# TAB 2: SETTINGS & MANAGEMENT
# ==========================
with tab_settings:
    st.header("⚙️ 设置与数据管理")
    
    # --- 1. Budget Settings ---
    with st.expander("💰 预算管理 (Budget Plans)", expanded=True):
        st.caption("设置每个分类的月度预算，将在首页展示进度条。")
        
        # Add New Budget (Refactored to Non-Form for Interactive Grid)
        if "new_budget_icon" not in st.session_state:
            st.session_state["new_budget_icon"] = "💰"

        c1, c2, c3 = st.columns(3)
        b_name = c1.text_input("预算名称", placeholder="例如：本月伙食", key="nb_name")
        b_cat = c2.selectbox("对应分类", options=CATEGORIES, key="nb_cat")
        b_amt = c3.number_input("预算金额", min_value=0.0, step=100.0, value=1000.0, key="nb_amt")
        
        c4, c5 = st.columns([1, 2])
        b_color = c4.color_picker("进度条颜色", "#FF4B4B", key="nb_color")
        
        with c5:
            st.markdown(f"**当前选择图标:** {st.session_state['new_budget_icon']}")

        # Icon Grid picker
        st.caption("选择图标 (点击选中):")
        EMOJI_OPTIONS = [
            "💰", "🍔", "🍜", "🍱", "🍷", "☕", "🍰", "🍎", "🥓", "🍳",  # 10
            "🚗", "🚕", "🚇", "✈️", "⛽", "🚲", "🏠", "💡", "💧", "🔌",  # 20
            "🛒", "🛍️", "👕", "👠", "📱", "💻", "🕶️", "💍", "💄", "🧴",  # 30
            "🍿", "🎮", "🎵", "🎨", "🎟️", "💊", "🏥", "🏋️", "👶", "🎁"   # 40
        ]
        
        # 10 cols grid
        cols = st.columns(10)
        for i, icon in enumerate(EMOJI_OPTIONS):
            with cols[i % 10]:
                # If selected, outline/primary, else secondary/ghost? 
                # Streamlit button styles are limited. primary = filled, secondary = outline/default.
                btn_type = "primary" if st.session_state["new_budget_icon"] == icon else "secondary"
                if st.button(icon, key=f"btn_icon_{i}", type=btn_type, width="stretch"):
                    st.session_state["new_budget_icon"] = icon
                    st.rerun()

        st.divider()

        if st.button("➕ 添加预算计划", type="primary", width="stretch"):
            if not b_name:
                st.error("请输入预算名称")
            else:
                if add_budget(b_name, b_cat, b_amt, b_color, st.session_state["new_budget_icon"]):
                    st.success("添加成功！")
                    # Reset basic fields manually if needed, or rely on rerun clearing
                    # But session state text inputs persist unless cleared.
                    # We can clear by setting keys in session state?
                    # Using key=... allows us to clear them:
                    # st.session_state["nb_name"] = "" ...
                    time.sleep(0.5)
                    st.rerun()

        # List Existing Budgets
        st.divider()
        st.markdown("##### 📜 已有预算清单")
        curr_budgets = get_budgets()
        if curr_budgets:
            for b in curr_budgets:
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    st.markdown(f"{b.get('icon','')} **{b['name']}** | {b['category']} | 预算: **${b['amount']}**")
                with col_del:
                    if st.button("删除", key=f"del_b_{b['id']}"):
                        if delete_budget(b['id']):
                            st.rerun()
        else:
            st.info("暂无预算，请添加。")

    # --- 2. Recurring Expenses ---
    with st.expander("🔄 固定开销 (Recurring Expenses)"):
        st.caption("设置定期自动扣款规则（如房租、订阅费）。需配合 Cloudflare Cron Trigger 使用。")
        
        # Add New Rule
        with st.form("add_recurring_form", clear_on_submit=True):
            r1, r2, r3 = st.columns(3)
            r_name = r1.text_input("名称", placeholder="例如：房租")
            r_amt = r2.number_input("金额", min_value=0.0, step=100.0, value=2000.0)
            r_cat = r3.selectbox("分类", options=CATEGORIES) # Manual '居住' might not strictly match but let's allow "其他" or expand list
            
            r4, r5 = st.columns(2)
            r_freq = r4.selectbox("频率", options=["weekly", "monthly", "yearly"])
            
            r_day_help = "Weekly: 1=周一...7=周日; Monthly: 1-31; Yearly: Day of Year (1-366)"
            r_day = r5.number_input("日期/星期 (Day)", min_value=1, max_value=366, value=1, help=r_day_help)
            
            if st.form_submit_button("➕ 添加固定规则"):
                if add_recurring(r_name, r_amt, r_cat, r_freq, r_day):
                    st.success("添加成功！")
                    st.rerun()
        
        # List Existing Rules (Editable)
        st.divider()
        st.markdown("##### 📜 运行中的规则 (支持编辑)")
        curr_rules = get_recurring_rules()
        
        if curr_rules:
            df_rules = pd.DataFrame(curr_rules)
            
            # 字段简单的预处理
            if "active" not in df_rules.columns:
                df_rules["active"] = 1
            
            # 将 active (1/0) 转为 bool 给 Checkbox 使用
            df_rules["启用"] = df_rules["active"].apply(lambda x: True if x == 1 else False)
            
            # 删除标记列
            df_rules.insert(0, "删除", False)
            
            if "id" in df_rules.columns:
                df_rules.set_index("id", inplace=True)

            # 配置列
            # Schema: name text, amount real, category text, frequency text, day integer, last_run_date text
            r_col_config = {
                "删除": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
                "启用": st.column_config.CheckboxColumn("✅", width="small", default=True),
                "name": st.column_config.TextColumn("名称", width="medium", required=True),
                "amount": st.column_config.NumberColumn("金额", min_value=0.0, format="$%.2f", width="small", required=True),
                "category": st.column_config.SelectboxColumn("分类", options=CATEGORIES, width="small", required=True),
                "frequency": st.column_config.SelectboxColumn("频率", options=["weekly", "monthly", "yearly"], width="small", required=True),
                "day": st.column_config.NumberColumn("日期/Day", width="small", min_value=1, max_value=366, required=True, help="Weekly:1-7; Monthly:1-31"),
                "last_run_date": st.column_config.TextColumn("上次运行", disabled=True, width="medium"),
            }
            
            # 显示的列
            r_show_cols = ["删除", "启用", "name", "amount", "category", "frequency", "day", "last_run_date"]
            
            edited_rules = st.data_editor(
                df_rules[r_show_cols],
                column_config=r_col_config,
                hide_index=True,
                width="stretch",
                key="recurring_editor"
            )
            
            # Save Logic
            r_to_delete_mask = edited_rules["删除"] == True
            r_delete_count = r_to_delete_mask.sum()
            
            r_editor_state = st.session_state.get("recurring_editor", {})
            r_edited_rows = r_editor_state.get("edited_rows", {})
            r_has_edits = len(r_edited_rows) > 0
            
            r_btn_label = "💾 保存规则修改"
            r_btn_type = "primary"
            if r_delete_count > 0:
                r_btn_label = f"🗑️ 确认删除 ({r_delete_count} 条)"
                r_btn_type = "secondary"
            
            if st.button(r_btn_label, type=r_btn_type, width="stretch", key="save_rules"):
                try:
                    r_changes = False
                    # 1. Delete
                    if r_delete_count > 0:
                        for rid, row in edited_rules[r_to_delete_mask].iterrows():
                             requests.post(f"{API_URL}/recurring/delete", json={"id": int(rid)}, headers={"X-API-Key": API_KEY})
                        st.success(f"已删除 {r_delete_count} 条规则")
                        r_changes = True
                    
                    # 2. Update
                    if r_has_edits:
                         for idx, changes in r_edited_rows.items():
                             row = edited_rules.iloc[idx]
                             if row["删除"]: continue
                             
                             payload = {
                                 "id": int(row.name),
                                 "name": row["name"],
                                 "amount": float(row["amount"]),
                                 "category": row["category"],
                                 "frequency": row["frequency"],
                                 "day": int(row["day"]),
                                 "active": bool(row["启用"])
                             }
                             requests.post(f"{API_URL}/recurring/update", json=payload, headers={"X-API-Key": API_KEY})
                         st.success("规则已更新")
                         r_changes = True
                    
                    if r_changes:
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"操作失败: {e}")
        else:
            st.info("暂无规则。")
        
        # Manual Trigger Button (For testing)
        if st.button("🛠️ 手动触发检查 (立即运行)"):
            try:
                chk = requests.get(f"{API_URL}/recurring/check", headers={"X-API-Key": API_KEY}, timeout=10)
                res = chk.json()
                st.success(f"检查完成，新增 {res.get('processed', 0)} 条记录")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # --- 3. Danger Zone (Moved here) ---
    with st.expander("🚨 危险区域 (Danger Zone)"):
        st.warning("清空所有数据，不可恢复！")
        confirm_clear = st.checkbox("确认清空所有数据")
        if st.button("💣 清空数据", type="secondary"):
            if confirm_clear:
                requests.post(f"{API_URL}/clear", headers={"X-API-Key": API_KEY})
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("请先确认")

