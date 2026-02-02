import pandas as pd
import streamlit as st

# ====== 配置 ======
SPREADSHEET_ID = "1s3JdFrzyfXMmJA7BRYK9xVsEASof_TxN3YMC8xbxW6E"
SHEET_NAME = "Ledger_Clean"  # 我们直接用 Clean 表，最干净
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

st.set_page_config(page_title="支出概览", layout="wide")

# ====== 读取数据 ======
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    # 只保留有效记录
    df = df[df["是否有效"] == True]
    return df

df = load_data()

# ====== 顶部 KPI ======
st.title("💰 支出概览")

col1, col2, col3 = st.columns(3)
col1.metric("本月支出", f"{df[df['月(yyyy-mm)'] == pd.Timestamp.today().strftime('%Y-%m')]['有效金额'].sum():,.0f}")
col2.metric("今年支出", f"{df[df['年'] == pd.Timestamp.today().year]['有效金额'].sum():,.0f}")
col3.metric("记录笔数", int(len(df)))

st.divider()

# ====== 图表 ======
left, right = st.columns(2)

with left:
    st.subheader("📈 月度趋势")
    month_sum = df.groupby("月(yyyy-mm)")["有效金额"].sum().reset_index()
    st.line_chart(month_sum, x="月(yyyy-mm)", y="有效金额")

with right:
    st.subheader("🥧 分类占比")
    cat_sum = df.groupby("分类")["有效金额"].sum().reset_index()
    st.dataframe(cat_sum, use_container_width=True)
    st.bar_chart(cat_sum, x="分类", y="有效金额")

# ====== 明细表 ======
st.subheader("📄 最近记录")
st.dataframe(
    df.sort_values("创建时间", ascending=False).head(20),
    use_container_width=True
)
