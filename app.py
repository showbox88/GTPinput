import time
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
from supabase import create_client, Client
import tempfile
import os
import json

# Optional imports
try:
    import expense_chat
except ImportError:
    pass

st.set_page_config(
    page_title="GTPinput",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ====== SUPABASE SETUP ======
# Initialize Supabase Client
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
# Use resource caching for the client might be better, but simple session restore works too
if "supabase_client" not in st.session_state:
    st.session_state["supabase_client"] = create_client(url, key)

supabase = st.session_state["supabase_client"]

# ====== AUTHENTICATION ======
SESSION_FILE = ".session_cache"

def save_session_to_file(session):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({
                "access_token": session.access_token,
                "refresh_token": session.refresh_token
            }, f)
    except Exception as e:
        st.error(f"Failed to save session: {e}")

def load_session_from_file():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                return data
        except:
            return None
    return None

def delete_session_file():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

if "session" not in st.session_state:
    st.session_state["session"] = None

# 1. Try to load from file if not in state
if not st.session_state["session"]:
    saved_session = load_session_from_file()
    if saved_session:
        try:
            res = supabase.auth.set_session(
                saved_session["access_token"], 
                saved_session["refresh_token"]
            )
            st.session_state["session"] = res.session
            st.session_state["user"] = res.user
        except Exception as e:
            delete_session_file() # Invalid token, clear it

# 2. If valid session exists, refresh it (supabase client handles auto-refresh usually, but good to be explicit if token is old)
if st.session_state["session"]:
    try:
        # If we just loaded from file, session is set. If from state, ensure client has it.
        # But set_session above already does it.
        pass 
    except Exception as e:
        st.session_state["session"] = None
        st.rerun()

def login_form():
    st.title("🔐 GTPinput 登录")
    
    tab_login, tab_signup = st.tabs(["登录 (Login)", "注册 (Sign Up)"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("邮箱 (Email)", key="login_email")
            password = st.text_input("密码 (Password)", type="password", key="login_password")
            remember = st.checkbox("保持登录 (Remember Me)", value=True)
            
            submitted = st.form_submit_button("登录", type="primary", width="stretch")
        
        if submitted:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["session"] = res.session
                st.session_state["user"] = res.user
                
                if remember:
                    save_session_to_file(res.session)
                
                st.rerun()
            except Exception as e:
                st.error(f"登录失败: {e}")
                
    with tab_signup:
        with st.form("signup_form"):
            s_email = st.text_input("邮箱 (Email)", key="signup_email")
            s_password = st.text_input("密码 (Password)", type="password", key="signup_password")
            submitted_s = st.form_submit_button("注册账号", width="stretch")
            
        if submitted_s:
            try:
                res = supabase.auth.sign_up({"email": s_email, "password": s_password})
                st.success("注册成功！请查收邮件确认，或直接登录（如果未开启邮箱验证）。")
            except Exception as e:
                st.error(f"注册失败: {e}")

if not st.session_state.get("session"):
    login_form()
    st.stop()

# Adding a logout button in sidebar
with st.sidebar:
    user_email = st.session_state["user"].email if st.session_state.get("user") else "Unknown"
    st.write(f"当前用户: {user_email}")
    if st.button("登出 (Logout)"):
        supabase.auth.sign_out()
        delete_session_file() # Clear local cache
        st.session_state["session"] = None
        st.session_state["user"] = None
        st.rerun()

# ====== DATA LOADING ======
@st.cache_data(ttl=5) # Short cache for responsiveness
def load_data() -> pd.DataFrame:
    try:
        # Supabase RLS automatically filters by user_id
        response = supabase.table("expenses").select("*").order("date", desc=True).order("id", desc=True).limit(500).execute()
        rows = response.data
        
        if not rows:
            return pd.DataFrame()
            
        df = pd.DataFrame(rows)
        
        # Data Cleaning
        if "amount" in df.columns:
            df["有效金额"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        
        if "date" in df.columns:
            df["日期"] = pd.to_datetime(df["date"], errors="coerce")
            df["月(yyyy-mm)"] = df["日期"].dt.strftime("%Y-%m")
            df["年"] = df["日期"].dt.year
            
        if "category" in df.columns:
            # Map legacy English categories to Chinese
            cat_map = {
                "Dining": "餐饮", "Food": "餐饮", 
                "Transport": "交通", "Transportation": "交通",
                "Shopping": "日用品", "Daily": "日用品",
                "Housing": "居住", "Home": "居住",
                "Medical": "医疗", "Health": "医疗",
                "Entertainment": "娱乐", "Fun": "娱乐",
                "Clothing": "服饰",
                "Others": "其他", "Other": "其他", "General": "其他"
            }
            # Apply map, keep original if not in map
            df["分类"] = df["category"].replace(cat_map)
            
            # Ensure all values are within the allowed list, otherwise default to "其他"
            # This prevents blank dropdowns in editor
            # (Optional: we can just trust the map + original values, but safer to standardize)
            allowed = set(CATEGORIES)
            df["分类"] = df["分类"].apply(lambda x: x if x in allowed else "其他")
            
        df["项目"] = df.get("item", "")
        df["备注"] = df.get("note", "")
        df["金额"] = df.get("amount", 0)
        df["来源"] = df.get("source", "")
        
        return df   
        
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

# ====== HELPER FUNCTIONS ======
def get_budgets():
    try:
        response = supabase.table("budgets").select("*").execute()
        return response.data
    except:
        return []

def add_budget(name, category, amount, color, icon):
    try:
        payload = {
            "name": name, 
            "category": category, 
            "amount": float(amount), 
            "color": color, 
            "icon": icon,
            "user_id": st.session_state["user"].id
        }
        supabase.table("budgets").insert(payload).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"添加失败: {e}")
        return False

def delete_budget(bid):
    try:
        supabase.table("budgets").delete().eq("id", bid).execute()
        st.cache_data.clear()
        return True
    except:
        return False

def get_recurring_rules():
    try:
        response = supabase.table("recurring_rules").select("*").eq("active", True).execute()
        return response.data
    except:
        return []

def add_recurring(name, amount, category, frequency, day):
    try:
        payload = {
            "name": name, 
            "amount": float(amount), 
            "category": category, 
            "frequency": frequency, 
            "day": int(day),
            "user_id": st.session_state["user"].id
        }
        supabase.table("recurring_rules").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"添加失败: {e}")
        return False

    try:
        supabase.table("recurring_rules").delete().eq("id", rid).execute()
        return True
    except:
        return False

def check_and_process_recurring():
    """
    Manually check if any recurring rules match today's date and add them if not already added this month.
    """
    try:
        rules = get_recurring_rules()
        if not rules:
            return "没有发现活跃的订阅规则。"
        
        today = pd.Timestamp.today()
        current_day = today.day
        current_month_str = today.strftime("%Y-%m")
        count_added = 0
        details = []

        for rule in rules:
            # 1. Check if today matches the rule's day (Simple Version: Only trigger on exact day or if force checked?)
            # Let's be smart: If today >= rule_day and no record exists for this month, add it.
            # This handles case where user forgets to check on the exact day.
            
            rule_day = rule.get("day", 1)
            
            # Simple Logic: If today is past or equal to the due day
            if current_day >= rule_day:
                # 2. Check if already added for this month
                # unique identifier: rule_id + month
                # We can query expenses with specific note format or just trust user?
                # Best way: Check expenses table for item == rule_name and date startswith current_month
                
                # Construct a query to find existing record
                # Note: This is an approximation. Ideally we have a linkage table. 
                # But for personal app, matching Name + Category + Amount + Month is sufficient.
                
                start_date = f"{current_month_str}-01"
                end_date = f"{current_month_str}-31" # Loose end date
                
                res = supabase.table("expenses") \
                    .select("*") \
                    .eq("item", rule["name"]) \
                    .eq("category", rule["category"]) \
                    .eq("amount", rule["amount"]) \
                    .gte("date", start_date) \
                    .lte("date", end_date) \
                    .execute()
                
                if not res.data:
                    # Not found -> Add it!
                    # Construct date: use this month's specific day
                    # Handle invalid days (e.g. Feb 30) -> limit to month end
                    try:
                        due_date = pd.Timestamp(year=today.year, month=today.month, day=rule_day)
                    except ValueError:
                         # Fallback to last day of month if day is invalid (e.g. 31st in Feb)
                         due_date = pd.Timestamp(year=today.year, month=today.month, day=1) + pd.offsets.MonthEnd(0)

                    payload = {
                        "date": due_date.strftime("%Y-%m-%d"),
                        "item": rule["name"],
                        "amount": float(rule["amount"]),
                        "category": rule["category"],
                        "note": "自动通过订阅规则生成 (Auto-Recurring)",
                        "source": "recurring_rule",
                        "user_id": st.session_state["user"].id
                    }
                    supabase.table("expenses").insert(payload).execute()
                    count_added += 1
                    details.append(f"✅ {rule['name']} (${rule['amount']})")
                else:
                    # Already exists
                    pass
        
        if count_added > 0:
            st.cache_data.clear()
            return f"成功添加 {count_added} 笔订阅支出:\n" + "\n".join(details)
        else:
            return "没有发现新的应扣费项目 (都已记录或未到期)。"

    except Exception as e:
        return f"检查失败: {e}"

# ==========================================
# CUSTOM WIDGETS
# ==========================================
def render_budget_progress(spent, limit):
    pct = spent / limit if limit > 0 else 0
    pct_clamped = min(pct, 1.0) * 100
    
    # Color Logic
    if pct > 1.0:
        # Over Budget: Red/Orange Gradient
        bar_color = "linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%)"
        text_color = "#FF4B2B"
    elif pct > 0.8:
        # Warning (80%+): Yellow/Orange
        bar_color = "linear-gradient(90deg, #F2994A 0%, #F2C94C 100%)" 
        text_color = "#F2994A"
    else:
        # Normal: Blue Gradient
        bar_color = "linear-gradient(90deg, #56CCF2 0%, #2F80ED 100%)"
        text_color = "#2F80ED"
        
    # HTML Component
    html = f"""
    <div style="margin-bottom: 2px;">
        <span style="font-weight:600; font-size:14px; color:{text_color if pct > 1.0 else 'inherit'}">
            ${spent:,.0f} / ${limit:,.0f}
        </span>
        <span style="float:right; font-size:12px; color:rgba(255,255,255,0.6)">{pct*100:.1f}%</span>
    </div>
    <div class="budget-bar-bg">
        <div class="budget-bar-fill" style="width: {pct_clamped}%; background: {bar_color};"></div>
    </div>
    """
    return html

# ==========================================
# Main App Layout
# ==========================================
CATEGORIES = ["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "居住", "其他"]

df = load_data()

# CSS Styling (Same as before)
st.markdown("""
<style>
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0E1117; }
    ::-webkit-scrollbar-thumb { background: #2E86C1; border-radius: 4px; }
    
    .stChatMessage { background-color: transparent !important; padding: 5px 0; }
    div[data-testid="stChatMessage"] { flex-direction: row !important; }
    div[data-testid="stChatMessage"] .stMarkdown {
        font-family: 'Inter', sans-serif; line-height: 1.6; padding: 12px 16px; max-width: 85%;
    }
    div[data-testid="stChatMessage"][aria-label="assistant"] .stMarkdown {
        background-color: #1E2530; border: 1px solid #2E86C1; border-radius: 0px 15px 15px 15px; color: #E0E0E0;
    }
    div[data-testid="stChatMessage"][aria-label="user"] .stMarkdown {
        background-color: #2E86C1; box-shadow: 0 4px 10px rgba(46, 134, 193, 0.2); border-radius: 15px 15px 15px 0px; color: white; margin-left: 10px;
    }
    .stChatInputContainer { border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; padding-bottom: 15px; background-color: #0E1117; }
    
    /* Typing Spinner Animation */
    .typing-spinner {
        display: inline-block;
        width: 24px;
        height: 24px;
        border: 3px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
        margin-left: 10px;
        vertical-align: middle;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Custom Budget Progress Bar */
    .budget-bar-bg {
        background-color: rgba(255, 255, 255, 0.1); 
        border-radius: 12px;
        width: 100%;
        height: 24px;
        margin: 5px 0;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .budget-bar-fill {
        height: 100%;
        border-radius: 12px;
        transition: width 0.6s ease;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    
    /* Carousel Animations - REMOVED */
</style>
""", unsafe_allow_html=True)

# Custom Navigation (Replaces st.tabs for stability)
st.markdown("""
<style>
    /* Radio Button Style to look like Tabs */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        width: 100%;
    }
    div[data-testid="stRadio"] label {
        background-color: transparent;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        transition: background 0.3s;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 0 5px;
        text-align: center;
        flex-grow: 1;
    }
    div[data-testid="stRadio"] label:hover {
        background-color: rgba(255,255,255,0.05);
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #2E86C1 !important;
        color: white !important;
        border-color: #2E86C1 !important;
    }
</style>
""", unsafe_allow_html=True)

main_nav = st.radio(
    "Navigation", 
    ["💬 智能输入", "📊 仪表盘", "⚙️ 设置"], 
    label_visibility="collapsed",
    horizontal=True,
    key="main_nav_radio"
)

# ==========================
# TAB 0: SMART INPUT (CHAT)
# ==========================
if main_nav == "💬 智能输入":
    c_head_1, c_head_2 = st.columns([0.85, 0.15])
    with c_head_1: st.subheader("💡 智能助手")
    with c_head_2:
        if st.button("🧼 清空", width="stretch"):
            st.session_state.messages = [{"role": "assistant", "content": "👋 嘿！我是你的智能财务管家。今天又花了什么钱？"}]
            st.rerun()

    # Draft Confirmation
    if "draft_expense" in st.session_state:
        draft = st.session_state["draft_expense"]
        with st.expander("📝 确认记账信息 (Confirm Receipt)", expanded=True):
            cols = st.columns([2, 1])
            with cols[0]:
                st.info(f"**{draft.get('item')}**")
                st.caption(f"分类: {draft.get('category')} | 日期: {draft.get('date')}")
            with cols[1]:
                st.metric("金额", f"{draft.get('amount')}")
            
            if st.button("✅ 确认保存", type="primary", width="stretch"):
                try:
                    payload = {
                        "date": draft.get('date'),
                        "item": draft.get('item'),
                        "amount": float(draft.get('amount', 0)),
                        "category": draft.get('category'),
                        "note": draft.get('note'),
                        "source": "camera_receipt",
                        "user_id": st.session_state["user"].id
                    }
                    supabase.table("expenses").insert(payload).execute()
                    st.success("已保存！")
                    del st.session_state["draft_expense"]
                    st.session_state["data_changed"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失败: {e}")

            if st.button("❌ 放弃"):
                del st.session_state["draft_expense"]
                st.rerun()

    # Chat History
    chat_container = st.container(height=500)
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "👋 嘿！我是你的智能财务管家。"}]

    with chat_container:
        for msg in st.session_state.messages:
            role = msg["role"]
            avatar = "https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput" if role == "assistant" else "https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123"
            st.chat_message(role, avatar=avatar).write(msg["content"])

    # File Upload / Camera
    col_tools_1, col_tools_2 = st.columns([0.1, 0.9])
    with col_tools_1:
         with st.popover("📎"):
            st.caption("上传单据/拍照")
            doc_file = st.file_uploader("File", label_visibility="collapsed")
            if doc_file and st.button("处理"):
                 # Simple placeholder for file logic - reuse previous logic if needed
                 st.info("图片处理逻辑参考之前版本...") 

    # Chat Input
    if prompt := st.chat_input("说点什么... (例如: 午饭 30)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.chat_message("user", avatar="https://api.dicebear.com/9.x/adventurer-neutral/svg?seed=user123").write(prompt)
        
        with chat_container:
            with st.chat_message("assistant", avatar="https://api.dicebear.com/9.x/bottts-neutral/svg?seed=gptinput"):
                response_placeholder = st.empty()
                response_placeholder.markdown("🤔 思考中... <span class='typing-spinner'></span>", unsafe_allow_html=True)

                # Use Local Logic for Streamlit
                result = expense_chat.process_user_message(prompt, df)
                intent_type = result.get("type", "chat")
                
                reply = ""
                if intent_type == "record":
                    # Handle single or multiple records
                    records_to_add = result.get("records", [])
                    if not records_to_add and "item" in result: 
                        # Fallback for single item response
                        records_to_add = [result]

                    if records_to_add:
                        payloads = []
                        success_items = []
                        
                        for r in records_to_add:
                            payloads.append({
                                "date": r.get("date"),
                                "item": r.get("item"),
                                "amount": float(r.get("amount", 0)),
                                "category": r.get("category", "其他"),
                                "note": r.get("note", ""),
                                "source": "chat_ui",
                                "user_id": st.session_state["user"].id
                            })
                            success_items.append(f"{r.get('item')} ({r.get('amount')})")

                        try:
                            if payloads:
                                supabase.table("expenses").insert(payloads).execute()
                                reply = f"✅ 已为您记录 {len(payloads)} 笔: {', '.join(success_items)}"
                                st.session_state["data_changed"] = True
                            else:
                                reply = "⚠️ 未识别到有效记录"
                        except Exception as e:
                            reply = f"❌ 记录失败: {e}"
                    else:
                        reply = "⚠️ 未识别到有效记录详情"

                elif intent_type == "delete":
                    try:
                        supabase.table("expenses").delete().eq("id", result["id"]).execute()
                        reply = "🗑️ 已删除指定记录。"
                        st.session_state["data_changed"] = True
                    except Exception as e:
                        reply = f"❌ 删除失败: {e}"

                elif intent_type == "update":
                    try:
                        supabase.table("expenses").update(result["updates"]).eq("id", result["id"]).execute()
                        reply = "✅ 已更新记录。"
                        st.session_state["data_changed"] = True
                    except Exception as e:
                        reply = f"❌ 更新失败: {e}"
                else:
                    reply = result.get("reply", "抱歉，我没听懂。")
                
                # Update placeholder with final reply
                response_placeholder.markdown(reply)
                
        # Persist to history
        st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.session_state.get("data_changed"):
        st.cache_data.clear()
        del st.session_state["data_changed"]
        st.rerun()

# ==========================
# TAB 1: DASHBOARD
# ==========================
# ====== SIDEBAR FILTERS ======
with st.sidebar:
    st.divider()
    st.header("筛选 (Filter)")
    months = sorted(df["月(yyyy-mm)"].dropna().unique().tolist()) if "月(yyyy-mm)" in df.columns else []
    sel_month = st.selectbox("月份", options=["全部"] + months, index=len(months) if months else 0)
    
    sel_categories = []
    if "分类" in df.columns:
        cats = sorted(df["分类"].dropna().unique().tolist())
        sel_categories = st.multiselect("分类", options=cats, default=[])

    if st.button("🔄 刷新数据 (Refresh)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Apply Filter
df_view = df.copy()
target_month_for_budget = pd.Timestamp.today().strftime("%Y-%m")

if sel_month != "全部":
    df_view = df_view[df_view["月(yyyy-mm)"] == sel_month] if "月(yyyy-mm)" in df_view.columns else df_view
    target_month_for_budget = sel_month

if sel_categories:
    df_view = df_view[df_view["分类"].isin(sel_categories)]

# ==========================
# TAB 1: DASHBOARD
# ==========================
if main_nav == "📊 仪表盘":
    if "dashboard_page" not in st.session_state:
        st.session_state.dashboard_page = 0
    # KPI
    this_month = pd.Timestamp.today().strftime("%Y-%m")
    month_total = df[df["月(yyyy-mm)"] == this_month]["有效金额"].sum() if "月(yyyy-mm)" in df.columns else 0
    k1, k2, k3 = st.columns(3)
    k1.metric("📅 本月支出", f"${month_total:,.2f}")
    k2.metric("🔍 筛选合计", f"${df_view['有效金额'].sum():,.2f}" if not df_view.empty else "$0.00")
    k3.metric("📝 记录笔数", f"{len(df_view)}")
    
    st.divider()
    
    # Carousel Navigation
    
    # Carousel Navigation
    # Use standard columns for navigation
    col_prev, col_title, col_next = st.columns([1, 4, 1])
    
    view_titles = ["📊 预算进度", "📈 月度趋势", "🥧 分类占比"]
    current_page = st.session_state.dashboard_page
    
    # 1. Render Buttons
    with col_prev:
        clicked_prev = st.button("⬅️", key="btn_prev", width="stretch")
            
    with col_next:
        clicked_next = st.button("➡️", key="btn_next", width="stretch")

    # 2. Render Title
    with col_title:
        st.markdown(f"<h3 style='text-align: center; margin: 0; padding: 0;'>{view_titles[current_page]}</h3>", unsafe_allow_html=True)
        
    # 3. Update State Logic
    # 3. Update State Logic
    if clicked_prev:
        st.session_state.dashboard_page = (st.session_state.dashboard_page - 1) % 3
        
    if clicked_next:
        st.session_state.dashboard_page = (st.session_state.dashboard_page + 1) % 3
        
    # Get Updated State
    current_page = st.session_state.dashboard_page

    # Carousel Frame (Fixed Height, Static Border)
    with st.container(height=400, border=True):
        if current_page == 0:
            # === BUDGET VIEW ===
            budgets = get_budgets()
            
            # Calculate budget spending based on the target month
            df_budget_calc = df.copy()
            if "月(yyyy-mm)" in df_budget_calc.columns:
                df_budget_calc = df_budget_calc[df_budget_calc["月(yyyy-mm)"] == target_month_for_budget]

            if budgets:
                # Use full width instead of columns for better mobile view in carousel
                for b in budgets:
                    spent = df_budget_calc[df_budget_calc["分类"] == b["category"]]["有效金额"].sum() if "分类" in df_budget_calc.columns else 0
                    limit = b["amount"]
                    
                    # Custom Progress Bar
                    st.markdown(f"**{b['category']}**")
                    progress_html = render_budget_progress(spent, limit)
                    st.markdown(progress_html, unsafe_allow_html=True)
                    st.write("") # Gap
            else:
                st.info("暂无预算，请在“设置”中添加。")

        elif current_page == 1:
            # === TREND VIEW ===
            if "月(yyyy-mm)" in df.columns and "有效金额" in df.columns:
                month_sum = df.groupby("月(yyyy-mm)", as_index=False)["有效金额"].sum().sort_values("月(yyyy-mm)")
                fig_bar = px.bar(month_sum, x="月(yyyy-mm)", y="有效金额", text_auto=".2s")
                fig_bar.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
                # Use dynamic key to force re-render and trigger animation
                st.plotly_chart(fig_bar, width="stretch", key=f"chart_trend_{current_page}")
            else:
                st.warning("暂无数据")

        elif current_page == 2:
            # === CATEGORY VIEW ===
            if not df_view.empty and "分类" in df_view.columns:
                cat_sum = df_view.groupby("分类", as_index=False)["有效金额"].sum().sort_values("有效金额", ascending=False)
                fig_pie = px.pie(cat_sum, names="分类", values="有效金额", hole=0.4)
                fig_pie.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), showlegend=True)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, width="stretch", key=f"chart_cat_{current_page}")
            else:
                st.warning("暂无数据")

    st.divider()

    # Data Editor
    st.subheader("📄 记录管理")
    if not df_view.empty:
        df_edit = df_view.copy()
        # Ensure ID is string for safety in editor index matching if needed, but int is fine usually
        df_edit["删除"] = False
        
        # We need 'id' in the dataframe but maybe hidden or read-only
        edit_cols = ["删除", "日期", "项目", "金额", "分类", "备注", "id"]
        
        # Configure columns
        col_cfg = {
            "删除": st.column_config.CheckboxColumn("🗑️", width="small", default=False),
            "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD", width="small"),
            "项目": st.column_config.TextColumn("项目", width="medium"),
            "金额": st.column_config.NumberColumn("金额", format="$%.2f", width="small"),
            "分类": st.column_config.SelectboxColumn("分类", options=CATEGORIES, width="small"),
            "备注": st.column_config.TextColumn("备注", width="medium"),
            "id": None # Hide ID column
        }
        
        # Wrap in form to prevent rerun on interaction (fix tab jump)
        with st.form("editor_form"):
            # Use a key to access state
            edited = st.data_editor(
                df_edit[edit_cols], 
                column_config=col_cfg, 
                hide_index=True, 
                num_rows="fixed", 
                key="editor",
                use_container_width=True
            )
            
            submit = st.form_submit_button("💾 保存修改 / 🗑️ 删除选中 (Submit Changes)", type="primary", use_container_width=True)
        
        if submit:
            changes_made = False
            
            # 1. Handle Deletes first
            # Re-fetch editor state from session state (or use return value 'edited' directly inside form logic context)
            # 'edited' variable holds the current state including user changes before submit if we use it here? 
            # Actually st.data_editor returns the state *after* interaction.
            # But inside form, it returns the state at the time of submit? Yes.
            
            to_delete = edited[edited["删除"] == True]
            delete_count = len(to_delete)
            
            if delete_count > 0:
                # Batch delete if possible, or loop
                ids_to_del = to_delete["id"].tolist()
                for d_id in ids_to_del:
                    supabase.table("expenses").delete().eq("id", d_id).execute()
                st.success(f"已删除 {delete_count} 条记录")
                changes_made = True
            
            # 2. Handle Updates
            # Check session state for edits
            # The 'editor' key in session_state contains 'edited_rows' dict: {row_index: {col_name: new_val}}
            # CAUTION: row_index corresponds to the dataframe passed to data_editor (df_edit)
            # Since df_edit might be filtered (df_view), we must rely on the index of df_edit matching the edited_rows keys.
            # Using .iloc[idx] on df_edit retrieves the correct original row.
            
            edits = st.session_state.get("editor", {}).get("edited_rows", {})
            if edits:
                for idx, changes in edits.items():
                    # Get ID of the row being edited
                    # Note: indices in edited_rows are integers 0..N relative to the displayed table
                    try:
                        row_id = df_edit.iloc[idx]["id"]
                        
                        # Prepare update payload
                        clean_changes = {}
                        if "日期" in changes: clean_changes["date"] = changes["日期"]
                        if "项目" in changes: clean_changes["item"] = changes["项目"]
                        if "金额" in changes: clean_changes["amount"] = changes["金额"]
                        if "分类" in changes: clean_changes["category"] = changes["分类"]
                        if "备注" in changes: clean_changes["note"] = changes["备注"]
                        
                        if clean_changes:
                            supabase.table("expenses").update(clean_changes).eq("id", row_id).execute()
                            changes_made = True
                    except IndexError:
                        pass # Should not happen if state is consistent
            
            if changes_made and delete_count == 0:
                st.success("修改已保存")
            
            if changes_made:
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()

# ==========================
# TAB 2: SETTINGS
# ==========================
if main_nav == "⚙️ 设置":
    st.header("⚙️ 设置")
    with st.expander("预算管理"):
        with st.form("add_budget"):
            c1, c2 = st.columns(2)
            b_cat = c1.selectbox("分类", CATEGORIES)
            b_amt = c2.number_input("限额", min_value=0)
            if st.form_submit_button("添加预算"):
                add_budget(f"{b_cat}预算", b_cat, b_amt, "#FF4B4B", "💰")
                st.rerun()
                
        # List budgets to delete/edit
        cur_budgets = get_budgets()
        if cur_budgets:
            df_budgets = pd.DataFrame(cur_budgets)
            # Ensure proper types
            if "amount" in df_budgets.columns:
                df_budgets["amount"] = pd.to_numeric(df_budgets["amount"], errors="coerce").fillna(0)
            
            # Configure editor
            b_cfg = {
                "category": st.column_config.SelectboxColumn("分类", options=CATEGORIES, required=True),
                "amount": st.column_config.NumberColumn("限额", min_value=0, step=100),
                "name": st.column_config.TextColumn("名称"),
                "id": None, "user_id": None, "icon": None, "color": None, "created_at": None
            }
            
            with st.form("budget_editor"):
                # Use data_editor with num_rows="dynamic" to allow adding/deleting rows directly? 
                # For now stick to strict editing existing, and keep the Add form separate for clarity unless merged.
                # Merging "Add" into the table is cleaner but requires handling new rows in backend.
                # Let's keep Add separate for now to avoid complexity, just allow Edit/Delete here.
                
                edited_b = st.data_editor(
                    df_budgets,
                    column_config=b_cfg,
                    use_container_width=True,
                    hide_index=True,
                    key="budget_editor",
                    num_rows="dynamic" # Allow delete
                )
                submit_b = st.form_submit_button("💾 保存预算修改 (Save Changes)")
            
            if submit_b:
                # 1. Handle Deletes
                # Find missing IDs
                current_ids = set(df_budgets["id"].tolist())
                new_ids_in_editor = set() 
                
                # Rows in edited_b might include new rows without ID (if added via table)
                # But if we only allow delete/edit existing:
                for idx, row in edited_b.iterrows():
                    if "id" in row and pd.notna(row["id"]):
                        new_ids_in_editor.add(row["id"])
                
                # IDs present before but missing now -> Deleted
                deleted_ids = current_ids - new_ids_in_editor
                for d_id in deleted_ids:
                    delete_budget(d_id)
                
                # 2. Handle Updates (and Adds if supported)
                # Check for changes
                # Since we wrapped in Form, 'edited_b' is the final state.
                # We can iterate and upsert.
                
                changes_count = 0
                for index, row in edited_b.iterrows():
                    # If it has an ID, it's an update
                    if "id" in row and pd.notna(row["id"]):
                        # Check if different from original
                        # Optimization: We could compare, or just upsert all for simplicity in this scale
                        
                        # Only update if fields changed - but simple upsert is fine for <50 items
                        try:
                            # Construct payload ensuring types
                            payload = {
                                "category": row["category"],
                                "amount": float(row["amount"]),
                                "name": row["name"]
                            }
                            supabase.table("budgets").update(payload).eq("id", row["id"]).execute()
                            changes_count += 1
                        except Exception as e:
                            st.error(f"Error updating budget {row.get('name')}: {e}")
                            
                if changes_count > 0 or len(deleted_ids) > 0:
                    st.success("预算设置已更新")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.caption("暂无预算设置")

    with st.expander("订阅/固定支出 (Recurring Expenses)"):
        st.write("设置每月/每年的固定支出。点击下方按钮可立即检查是否需要扣款。")
        
        c_check, c_dummy = st.columns([1, 2])
        if c_check.button("🔄 立即检查今日应扣费 (Check Now)"):
           with st.spinner("检查中..."):
               res_msg = check_and_process_recurring()
               if "成功" in res_msg:
                   st.success(res_msg)
                   time.sleep(2)
                   st.rerun()
               else:
                   st.info(res_msg)
        
        # Add New Rule
        with st.form("add_recurring"):
            cols = st.columns(4)
            r_name = cols[0].text_input("名称 (e.g. Netflix)")
            r_amt = cols[1].number_input("金额", min_value=0.0, step=1.0)
            r_cat = cols[2].selectbox("分类", CATEGORIES, key="r_cat")
            r_freq = cols[3].selectbox("周期", ["Monthly", "Yearly"])
            r_day = st.number_input("扣款日 (Day of Month)", min_value=1, max_value=31, value=1)
            
            if st.form_submit_button("添加订阅"):
                add_recurring(r_name, r_amt, r_cat, r_freq, r_day)
                st.success(f"已添加: {r_name}")
                time.sleep(1)
                st.rerun()

        # List Rules
        rules = get_recurring_rules()
        if rules:
            st.write("📋 订阅管理 (Edit/Delete):")
            df_rules = pd.DataFrame(rules)
            
             # Configure editor
            r_cfg = {
                "name": st.column_config.TextColumn("名称", required=True),
                "amount": st.column_config.NumberColumn("金额", min_value=0.0, step=1.0, required=True),
                "category": st.column_config.SelectboxColumn("分类", options=CATEGORIES, required=True),
                "frequency": st.column_config.SelectboxColumn("周期", options=["Monthly", "Yearly"], required=True),
                "day": st.column_config.NumberColumn("扣款日", min_value=1, max_value=31),
                "id": None, "user_id": None, "active": None, "created_at": None, "last_triggered": None
            }
            
            with st.form("rule_editor"):
                edited_r = st.data_editor(
                    df_rules,
                    column_config=r_cfg,
                    use_container_width=True,
                    hide_index=True,
                    key="rule_editor",
                    num_rows="dynamic"
                )
                submit_r = st.form_submit_button("💾 保存订阅修改 (Save Changes)")
                
            if submit_r:
                # 1. Deletes
                cur_r_ids = set(df_rules["id"].tolist())
                new_r_ids = set()
                for idx, row in edited_r.iterrows():
                    if "id" in row and pd.notna(row["id"]):
                        new_r_ids.add(row["id"])
                
                del_r_ids = cur_r_ids - new_r_ids
                for d_id in del_r_ids:
                    delete_recurring(d_id)
                
                # 2. Updates
                r_changes = 0
                for index, row in edited_r.iterrows():
                    if "id" in row and pd.notna(row["id"]):
                         try:
                            payload = {
                                "name": row["name"],
                                "amount": float(row["amount"]),
                                "category": row["category"],
                                "frequency": row["frequency"],
                                "day": int(row["day"])
                            }
                            supabase.table("recurring_rules").update(payload).eq("id", row["id"]).execute()
                            r_changes += 1
                         except Exception as e:
                            st.error(f"Error updating rule {row.get('name')}: {e}")
                
                if r_changes > 0 or len(del_r_ids) > 0:
                     st.success("订阅规则已更新")
                     time.sleep(1)
                     st.rerun()

        else:
            st.caption("暂无固定支出")

    with st.expander("数据导出 (Export Data)"):
        st.write("将所有账单数据导出为 CSV 文件。")
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8-sig') # BOM for Excel compatibility
            st.download_button(
                "📥 下载 CSV",
                csv,
                "expenses_backup.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.warning("暂无数据可导出")
