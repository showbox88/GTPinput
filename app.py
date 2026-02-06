import time
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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

# ====== CUSTOM CSS & THEME OVERRIDES ======
st.markdown("""
<style>
    /* Global Professional Dark Theme Enhancements */
    
    /* Smooth Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0E1117; 
    }
    ::-webkit-scrollbar-thumb {
        background: #2E86C1; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #1B4F72; 
    }

    /* -------------------------
       CHAT BUBBLES & LAYOUT
       ------------------------- */
    
    /* Global Chat settings */
    .stChatMessage {
        background-color: transparent !important;
        padding: 5px 0;
    }

    /* USER MESSAGE: Force alignment to LEFT */
    div[data-testid="stChatMessage"] {
        flex-direction: row !important; /* Force Avatar Left, Content Right for everyone including User */
    }

    /* Message Content Styling */
    div[data-testid="stChatMessage"] .stMarkdown {
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
        padding: 12px 16px;
        max-width: 85%;
        position: relative;
    }

    /* 🧠 Assistant Bubble (Right of Avatar) */
    div[data-testid="stChatMessage"][aria-label="assistant"] .stMarkdown {
        background-color: #1E2530; 
        border: 1px solid #2E86C1;
        border-radius: 0px 15px 15px 15px; /* Top-Left square */
        color: #E0E0E0;
    }

    /* 👤 User Bubble (Blue Theme) */
    div[data-testid="stChatMessage"][aria-label="user"] .stMarkdown {
        background-color: #2E86C1; 
        box-shadow: 0 4px 10px rgba(46, 134, 193, 0.2);
        border-radius: 15px 15px 15px 0px; 
        color: white;
        border-radius: 15px 15px 15px 0px; 
        margin-left: 10px;
    }

    /* Input Area - Integrated Look */
    .stChatInputContainer {
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 15px;
        padding-bottom: 15px;
        background-color: #0E1117; 
    }
    
    /* Button Overrides */
    .stButton button[kind="primary"] {
        background: linear-gradient(90deg, #2E86C1 0%, #1B4F72 100%);
        border: none;
        box-shadow: 0 4px 10px rgba(46, 134, 193, 0.3);
        transition: all 0.3s ease;
    }
    .stButton button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(46, 134, 193, 0.5);
    }

    /* File Uploader Customization */
    [data-testid="stFileUploader"] {
        border: 1px dashed #2E86C1;
        border-radius: 10px;
        background-color: rgba(46, 134, 193, 0.05);
    }

</style>
""", unsafe_allow_html=True)

tab_chat, tab_dash, tab_settings = st.tabs(["💬 智能输入", "📊 仪表盘", "⚙️ 设置"])

# ==========================
# TAB 0: SMART INPUT (CHAT)
# ==========================
with tab_chat:
    # Custom Header Layout
    c_head_1, c_head_2 = st.columns([0.85, 0.15])
    with c_head_1:
         st.subheader("💡 智能助手")
    with c_head_2:
         # Clear chat button
         if st.button("🧼 清空", help="清空当前对话历史", use_container_width=True):
             # Reset to engaging welcome message
             welcome_txt = "👋 嘿！我是你的智能财务管家。\n\n今天又发现了什么好东西？或者……又要为“剁手”记账了？💸\n\n你可以说：\n- **“记录午饭沙县小吃 25”**\n- **“把刚才的 25 改成 28”**\n- **“上周我在交通上花了多少？”**"
             st.session_state.messages = [{"role": "assistant", "content": welcome_txt}]
             st.rerun()

    # --- 1. Scrollable Chat Container (Fixed Height) ---
    chat_container = st.container(height=500)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Engaging Welcome Message (Init)
        welcome_txt = "👋 嘿！我是你的智能财务管家。\n\n今天又发现了什么好东西？或者……又要为“剁手”记账了？💸\n\n你可以说：\n- **“记录午饭沙县小吃 25”**\n- **“把刚才的 25 改成 28”**\n- **“上周我在交通上花了多少？”**"
        st.session_state.messages.append({"role": "assistant", "content": welcome_txt})

    with chat_container:
        for msg in st.session_state.messages:
            # Use consistent dicebear avatars (SVG)
            # Bot: Robot style | User: Person style
            if msg["role"] == "assistant":
                avatar_url = "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput"
            else:
                avatar_url = "https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123"
            
            st.chat_message(msg["role"], avatar=avatar_url).write(msg["content"])

    # --- 2. Integrated Interaction Area (Upload + Input) ---
    # Use columns to position the upload button near the input area conceptually
    
    # Tool Bar above Input
    col_tools_1, col_tools_2 = st.columns([0.1, 0.9])
    
    with col_tools_1:
        # Compact Popover for Upload
        with st.popover("📎", help="上传单据/证件 (SmartDoc)"):
            st.markdown("### 📤 上传附件")
            
            # Use tabs for File vs Camera
            tab_file, tab_cam = st.tabs(["📂 文件", "📸 拍照"])
            
            final_file = None
            
            with tab_file:
                u_file = st.file_uploader("选择文件", type=["png", "jpg", "jpeg", "webp", "pdf"], key="sl_uploader", label_visibility="collapsed")
                if u_file: final_file = u_file
                
            with tab_cam:
                # Lazy load to prevent immediate permission request
                if st.checkbox("🔌 启动相机 (Start Camera)", key="enable_camera"):
                    st.caption("📱 **提示**：如需切换前后镜头，请使用相机画面上的翻转按钮")
                    c_file = st.camera_input("拍照", label_visibility="collapsed")
                    if c_file: final_file = c_file

            if final_file:
                # Show preview if image
                # if final_file.type.startswith("image"):
                #     st.image(final_file, width=150)
                
                if st.button(f"🚀 上传处理: {final_file.name}", key="btn_upload_process", type="primary", use_container_width=True):
                    with st.status("正在处理...", expanded=True) as status:
                        # Save to temp
                        # Handle potential missing explicit name in camera_input (often 'camera_input.jpg' or similar)
                        fname = final_file.name if hasattr(final_file, 'name') else "camera_capture.jpg"
                        
                        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f".{fname.split('.')[-1]}")
                        tfile.write(final_file.read())
                        tfile.close()
                        temp_path = tfile.name
                        
                        status.write("🤖 AI 识别中...")
                        try:
                            ai = AIProcessor()
                            res = ai.analyze_image(temp_path)
                            
                            if res.get("type") == "ERROR":
                                st.error(f"识别失败: {res.get('name')}")
                            else:
                                st.success("识别成功")
                                
                                # Prepare data for upload
                                save_data = res.copy()
                                save_data['original_filename'] = fname
                                save_data['temp_path'] = temp_path
                                save_data['extension'] = fname.split('.')[-1]
                                save_data['name'] = res.get('name', 'Unknown')
                                
                                # Upload
                                gs = GoogleService()
                                folder_hint = FOLDER_MAP.get(res.get('type'), FOLDER_MAP["OTHER"])
                                new_name = generate_filename(save_data)
                                
                                link = gs.upload_file(temp_path, new_name, folder_hint)
                                
                                # Sheet & Calendar
                                sheet_row = [
                                    str(pd.Timestamp.today().date()),
                                    save_data.get('name'),
                                    save_data.get('type'),
                                    save_data.get('doc_id'),
                                    save_data.get('expiry_date'),
                                    "N/A", 
                                    "Skipped",
                                    link
                                ]
                                gs.append_to_sheet(sheet_row)
                                
                                # Sync to Expense
                                try:
                                    extract_amt = save_data.get('amount', 0)
                                    if isinstance(extract_amt, (int, float)) and extract_amt > 0:
                                        s_item = save_data.get('name', 'SmartDoc Item')
                                        s_cat = save_data.get('category', '其他')
                                        s_date = pd.Timestamp.today().strftime("%Y-%m-%d")
                                        syn_text = f"{s_item} {extract_amt} {s_cat} SmartDoc-Auto-Sync Date:{s_date}"
                                        requests.post(f"{API_URL}/add", json={"text": syn_text, "source": "smart_doc_upload"}, headers={"X-API-Key": API_KEY})
                                        st.caption(f"💰 已同步账本: ${extract_amt}")
                                        st.session_state["data_changed"] = True
                                except:
                                    pass
                                
                                if save_data.get('expiry_date') != "N/A":
                                    gs.add_calendar_reminder(f"{save_data['name']} {save_data['type']}", save_data['expiry_date'], 7)
                                    
                                status.update(label="✅ 归档完成", state="complete", expanded=False)
                                
                                # Post message to chat
                                st.session_state.messages.append({"role": "assistant", "content": f"✅ 文件 **{save_data['name']}** 已成功归档！[查看连接]({link})"})
                                st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")
                            st.exception(e) # More detailed error
                        
                        try:
                            # Cleanup
                            # os.remove(temp_path) # Might fail if still held
                            pass
                        except:
                            pass

    # --- 3. Chat Input (Pinned Bottom) ---
    if prompt := st.chat_input("说点什么... (例如: 午饭 30)"):
        # Add User Message to State
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Write to container immediately
        with chat_container:
            st.chat_message("user", avatar="https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123").write(prompt)
        
        # Process logic
        with st.spinner("Thinking..."):
            result = expense_chat.process_user_message(prompt, df)
            intent_type = result.get("type", "chat")
            
            # Record Intent
            if intent_type == "record":
                 item_str = result.get('item', 'Unknown')
                 amt_str = str(result.get('amount', 0))
                 date_str = result.get('date', pd.Timestamp.today().strftime("%Y-%m-%d"))
                 cat_str = result.get('category', '其他')
                 note_str = result.get('note', '')
                 
                 synthetic_text = f"{item_str} {amt_str} {cat_str} {note_str} Date:{date_str}"
                 try:
                     resp = requests.post(f"{API_URL}/add", json={"text": synthetic_text, "source": "chat_ui"}, headers={"X-API-Key": API_KEY})
                     if resp.status_code == 200:
                         reply = f"✅ 已为您记录: **{item_str}** ${amt_str} ({cat_str})"
                         st.session_state["data_changed"] = True
                     else:
                         reply = f"❌ 记录失败: {resp.text}"
                 except Exception as e:
                     reply = f"❌ 错误: {e}"
                 
                 st.session_state.messages.append({"role": "assistant", "content": reply})
                 with chat_container:
                     st.chat_message("assistant", avatar="https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput").write(reply)

            # Delete Intent     
            elif intent_type == "delete":
                del_id = result.get("id")
                if del_id:
                    try:
                        resp = requests.post(f"{API_URL}/delete", json={"id": int(del_id)}, headers={"X-API-Key": API_KEY})
                        if resp.status_code == 200:
                             reply = f"🗑️ 已删除 ID: {del_id} 的记录"
                             st.session_state["data_changed"] = True
                        else:
                             reply = f"❌ 删除失败: {resp.text}"
                    except Exception as e:
                         reply = f"❌ 错误: {e}"
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    with chat_container:
                        st.chat_message("assistant").write(reply)

            # Update Intent
            elif intent_type == "update":
                upd_id = result.get("id")
                updates = result.get("updates", {})
                
                if upd_id and updates:
                    try:
                        # 1. Find original row from df
                        # We need to find the row with 'id' == upd_id
                        # df might be missing 'id' column if empty, handle that
                        if not df.empty and "id" in df.columns:
                            original_row = df[df["id"] == upd_id]
                            if not original_row.empty:
                                row_data = original_row.iloc[0].to_dict()
                                
                                # 2. Merge updates
                                # Map friendly update keys to API keys just in case? 
                                # API uses: date, item, amount, category, note, id
                                # Chat output uses: date, item, amount, category, note
                                # Should match directly.
                                
                                # Construct full payload from original + updates
                                payload = {
                                    "id": int(upd_id),
                                    "date": updates.get("date", row_data.get("date", row_data.get("日期"))), # Fallback to various data shapes
                                    "item": updates.get("item", row_data.get("item", row_data.get("项目"))),
                                    "amount": float(updates.get("amount", row_data.get("amount", row_data.get("金额")))),
                                    "category": updates.get("category", row_data.get("category", row_data.get("分类"))),
                                    "note": updates.get("note", row_data.get("note", row_data.get("备注")))
                                }
                                
                                # 3. Send Update
                                resp = requests.post(f"{API_URL}/update", json=payload, headers={"X-API-Key": API_KEY})
                                if resp.status_code == 200:
                                     reply = f"✅ 已修改记录 {upd_id}: "
                                     if "amount" in updates: reply += f"金额->{payload['amount']} "
                                     if "item" in updates: reply += f"项目->{payload['item']} "
                                     if "category" in updates: reply += f"分类->{payload['category']} "
                                     
                                     st.session_state["data_changed"] = True
                                else:
                                     reply = f"❌ 修改失败: {resp.text}"
                            else:
                                reply = f"⚠️ 找不到 ID: {upd_id} 的原始记录，无法修改。"
                        else:
                             reply = "⚠️ 本地数据未同步，无法执行修改，请刷新页面重试。"
                    
                    except Exception as e:
                         reply = f"❌ 错误: {e}"
                else:
                    reply = "⚠️ 无法识别需要修改的信息。"
                
                st.session_state.messages.append({"role": "assistant", "content": reply})
                with chat_container:
                    st.chat_message("assistant").write(reply)


            # Normal Chat
            else: # type == chat
                reply = result.get("reply", "抱歉，我没听懂。")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                with chat_container:
                    st.chat_message("assistant").write(reply)

    if st.session_state.get("data_changed"):
        st.cache_data.clear()
        del st.session_state["data_changed"]
        st.rerun()

    # JS Hack to auto-focus the chat input after rerun
    st.components.v1.html(
        """
        <script>
            var text_input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (text_input) {
                text_input.focus();
            }
        </script>
        """,
        height=0,
        width=0,
    )


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

