import time
import pandas as pd
import streamlit as st
import plotly.express as px

import requests

# ====== 配置 (从 secrets 读取) ======
# 需要在 .streamlit/secrets.toml 中配置 API_URL 和 API_KEY
API_URL = st.secrets["general"]["API_URL"]
API_KEY = st.secrets["general"]["API_KEY"]

st.set_page_config(page_title="支出概览", layout="wide")

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

# ====== 顶部工具条 ======
top_left, top_right = st.columns([1, 4])
with top_left:
    if st.button("🔄 立即刷新"):
        st.cache_data.clear()
        time.sleep(0.2)
        st.rerun()

st.title("💰 支出概览")

df = load_data()

if df.empty:
    st.info("还没有可统计的数据（是否有效=True 的记录为空）。先记几笔再来看图表。")
    st.stop()

# ====== 侧边栏筛选 ======
st.sidebar.header("筛选")
months = sorted(df["月(yyyy-mm)"].dropna().unique().tolist()) if "月(yyyy-mm)" in df.columns else []
default_month = months[-1] if months else None

sel_month = st.sidebar.selectbox("月份", options=["全部"] + months, index=(len(months) if months else 0))
sel_categories = None
if "分类" in df.columns:
    cats = sorted(df["分类"].dropna().unique().tolist())
    sel_categories = st.sidebar.multiselect("分类（可多选）", options=cats, default=[])

# 应用筛选
df_view = df.copy()
if sel_month != "全部" and "月(yyyy-mm)" in df_view.columns:
    df_view = df_view[df_view["月(yyyy-mm)"] == sel_month]

if sel_categories:
    df_view = df_view[df_view["分类"].isin(sel_categories)]

# ====== KPI ======
k1, k2, k3, k4 = st.columns(4)

# 本月（按今天所属月）
this_month = pd.Timestamp.today().strftime("%Y-%m")
this_year = pd.Timestamp.today().year

month_total = df[df["月(yyyy-mm)"] == this_month]["有效金额"].sum() if "月(yyyy-mm)" in df.columns else 0
year_total = df[df["年"] == this_year]["有效金额"].sum() if "年" in df.columns else 0
view_total = df_view["有效金额"].sum()

k1.metric("本月支出", f"{month_total:,.0f}")
k2.metric("今年支出", f"{year_total:,.0f}")
k3.metric("当前筛选合计", f"{view_total:,.0f}")
k4.metric("记录笔数（筛选后）", f"{len(df_view)}")

st.divider()

# ====== 图表区：左趋势 右饼图 ======
left, right = st.columns([2, 1])

with left:
    st.subheader("📈 月度趋势（总支出）")
    if "月(yyyy-mm)" in df.columns:
        month_sum = df.groupby("月(yyyy-mm)", as_index=False)["有效金额"].sum().sort_values("月(yyyy-mm)")
        fig_line = px.line(month_sum, x="月(yyyy-mm)", y="有效金额", markers=True)
        fig_line.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=360)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("找不到列：月(yyyy-mm)")

with right:
    st.subheader("🥧 分类占比（筛选后）")
    if "分类" in df_view.columns:
        cat_sum = df_view.groupby("分类", as_index=False)["有效金额"].sum().sort_values("有效金额", ascending=False)
        if cat_sum.empty:
            st.info("当前筛选条件下没有数据。")
        else:
            fig_pie = px.pie(cat_sum, names="分类", values="有效金额", hole=0.35)
            fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=360, legend_title_text="分类")
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("找不到列：分类")

st.divider()

# ====== 最近记录表 ======
st.subheader("📄 最近记录（筛选后）")
# 动态调整显示列，确保列存在
all_possible_cols = ["日期", "项目", "金额", "分类", "来源", "备注", "创建时间", "有效金额"]
show_cols = [c for c in all_possible_cols if c in df_view.columns]

df_recent = df_view.sort_values("创建时间", ascending=False) if "创建时间" in df_view.columns else df_view
st.dataframe(df_recent[show_cols].head(50), use_container_width=True, hide_index=True)
