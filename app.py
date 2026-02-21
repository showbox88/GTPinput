import streamlit as st
from supabase import create_client
import modules.auth as auth

import modules.ui_v2 as ui_v2
import modules.i18n as i18n

# 1. Page Config (Must be first)
st.set_page_config(
    page_title="智能记账小助手",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Supabase Setup
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
except FileNotFoundError:
    st.error("Secrets file not found. Please set up .streamlit/secrets.toml")
    st.stop()

if "supabase_client" not in st.session_state:
    st.session_state["supabase_client"] = create_client(url, key)
supabase = st.session_state["supabase_client"]

# 3. Authentication Check
if "session" not in st.session_state:
    st.session_state["session"] = None

if not st.session_state["session"]:
    session, user = auth.restore_session(supabase)
    if session:
        st.session_state["session"] = session
        st.session_state["user"] = user
    else:
        st.session_state["session"] = None

# 4. Initialize i18n before rendering Login UI to support localization
# Fallback to 'zh' if not determined yet
try:
    # If user is logged in, use their preference. If not, default to 'zh'.
    user_lang = "zh"
    if "user" in st.session_state and st.session_state["user"]:
        user_lang = st.session_state["user"].user_metadata.get("language", "zh")
    i18n.init_i18n(user_lang)
except Exception:
    i18n.init_i18n("zh")

# 5. Login Form (If not logged in)
if not st.session_state.get("session"):
    st.title(f"🔐 {i18n._('nav_floating_home')} - GTPinput")
    
    tab_login, tab_signup = st.tabs([f"{i18n._('settings_logout').split(' ')[1]} (Login)", "注册 (Sign Up)"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input(i18n._("settings_email"), key="login_email")
            password = st.text_input("密码 (Password)", type="password", key="login_password")
            remember = st.checkbox("保持登录 (Remember Me)", value=True)
            submitted = st.form_submit_button(i18n._("settings_logout").split(" ")[1], type="primary", width="stretch")
        
        if submitted:
            try:
                res = auth.sign_in(supabase, email, password, remember)
                st.session_state["session"] = res.session
                st.session_state["user"] = res.user
                if "messages" in st.session_state:
                    del st.session_state["messages"]
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
                auth.sign_up(supabase, s_email, s_password)
                st.success("注册成功！请查收邮件确认，或直接登录（如果未开启邮箱验证）。")
            except Exception as e:
                st.error(f"注册失败: {e}")
    
    st.stop()

# 6. Re-Initialize i18n with user specific language if just logged in
if "user" in st.session_state and st.session_state["user"]:
    user_lang = st.session_state["user"].user_metadata.get("language", "zh")
    i18n.init_i18n(user_lang)

# 7. Render UI (V2 Only)
ui_v2.render(supabase)
