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
    # 这里不能直接 stop，否则无法显示清空按钮（虽然没数据也就不用清空，但为了逻辑完整）
    # st.stop() 

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

# 安全获取 sum，防止 Key Error
def safe_sum(dataframe, col):
    if col in dataframe.columns:
        return dataframe[col].sum()
    return 0

month_total = df[df["月(yyyy-mm)"] == this_month]["有效金额"].sum() if "月(yyyy-mm)" in df.columns and "有效金额" in df.columns else 0
year_total = df[df["年"] == this_year]["有效金额"].sum() if "年" in df.columns and "有效金额" in df.columns else 0
view_total = safe_sum(df_view, "有效金额")

k1.metric("📅 本月支出", f"${month_total:,.2f}")
k2.metric("🗓️ 今年支出", f"${year_total:,.2f}")
k3.metric("🔍 当前筛选合计", f"${view_total:,.2f}")
k4.metric("📝 记录笔数", f"{len(df_view)}")

st.divider()

# ====== 图表区：左趋势 右饼图 ======
# 移动端适配：st.columns 在手机上会垂直堆叠，默认行为
left, right = st.columns([2, 1])

with left:
    st.subheader("📈 月度趋势")
    if "月(yyyy-mm)" in df.columns and "有效金额" in df.columns:
        month_sum = df.groupby("月(yyyy-mm)", as_index=False)["有效金额"].sum().sort_values("月(yyyy-mm)")
        # 改为柱状图 (Bar Chart)
        fig_bar = px.bar(month_sum, x="月(yyyy-mm)", y="有效金额", text_auto=".2s")
        fig_bar.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
        fig_bar.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=300,
            xaxis_title="",
            yaxis_title="金额 ($)",
            yaxis_tickprefix="$"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
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
                showlegend=False # 手机上隐藏图例更清晰
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("暂无分类数据")

st.divider()

# ====== 最近记录表 (支持修改/删除) ======
st.subheader("📄 最近记录")

# 准备编辑的数据
# 确保 ID 存在，用于 API 调用
if not df_view.empty:
    # 构造显示的 DataFrame
    df_editor = df_view.copy()
    
    # 核心修正：将 ID 设为 Index，这样 st.data_editor(hide_index=True) 就能隐藏 ID，
    # 同时保留 ID 用于后续逻辑 (通过 row.name 获取)
    if "id" in df_editor.columns:
        df_editor.set_index("id", inplace=True)
    
    # 添加一个 "删除" 勾选列，默认 False
    if "删除" not in df_editor.columns:
        df_editor.insert(0, "删除", False)

    # 需要显示的列（ID是索引，不需要在 columns 里写）
    show_cols = ["删除", "日期", "项目", "金额", "分类", "备注"]
    
    # 确保列存在
    final_cols = [c for c in show_cols if c in df_editor.columns]
    
    # 配置列编辑器
    column_config = {
        "删除": st.column_config.CheckboxColumn(
            "🗑️",
            width="small",
            default=False,
            help="勾选删除"
        ),
        # ID 不在 columns 里了，不需要配置
        "日期": st.column_config.DateColumn(
            "日期",
            format="YYYY-MM-DD",
            required=True,
            width="small"
        ),
        "项目": st.column_config.TextColumn("项目", width="medium"),
        "金额": st.column_config.NumberColumn(
            "金额",
            min_value=0,
            format="$%.2f",
            required=True,
            width="small"
        ),
        "分类": st.column_config.SelectboxColumn(
            "分类",
            options=["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "其他"],
            required=True,
            width="small"
        ),
        "备注": st.column_config.TextColumn("备注", width="medium")
    }

    # 按照创建时间倒序排
    if "创建时间" in df_editor.columns:
        df_editor = df_editor.sort_values("创建时间", ascending=False)

    # 显示编辑器
    edited_df = st.data_editor(
        df_editor[final_cols],
        column_config=column_config,
        hide_index=True, # 隐藏 Index (即 ID)
        use_container_width=True,
        num_rows="fixed",
        key="expense_editor"
    )

    # 操作按钮区
    to_delete_mask = edited_df["删除"] == True
    delete_count = to_delete_mask.sum()
    
    # 检查是否有编辑
    editor_state = st.session_state.get("expense_editor", {})
    edited_rows_dict = editor_state.get("edited_rows", {})
    has_edits = len(edited_rows_dict) > 0
    
    btn_label = "💾 保存修改"
    btn_type = "primary"
    
    if delete_count > 0:
        btn_label = f"🗑️ 确认删除 ({delete_count} 条)"
        btn_type = "secondary" 
    elif has_edits:
        btn_label = "💾 保存修改"
    
    if st.button(btn_label, type=btn_type, use_container_width=True):
        try:
            changes_made = False
            
            # 1. Delete Logic
            if delete_count > 0:
                to_delete = edited_df[to_delete_mask]
                success_del = 0
                for rec_id, row in to_delete.iterrows():
                    # 因为 ID 是 Index，所以 rec_id 就是 ID
                    # 确保是 int
                    safe_id = int(rec_id)
                    
                    del_url = f"{API_URL}/delete"
                    resp = requests.post(del_url, json={"id": safe_id}, headers={"X-API-Key": API_KEY}, timeout=10)
                    
                    if resp.status_code == 200:
                        success_del += 1
                    else:
                        st.error(f"删除失败 ID {safe_id}")
                
                if success_del > 0:
                    st.success(f"已删除 {success_del} 条记录")
                    changes_made = True

            # 2. Update Logic
            if has_edits:
                update_count = 0
                for idx, changes in edited_rows_dict.items():
                    # idx: index in edited_df (integer position)
                    row = edited_df.iloc[idx]
                    
                    if row["删除"]: continue 
                    
                    # ID 是 Index
                    safe_id = int(row.name)
                    
                    payload = {
                        "id": safe_id,
                        "date": row["日期"].strftime("%Y-%m-%d") if hasattr(row["日期"], "strftime") else str(row["日期"]),
                        "item": row["项目"],
                        "amount": float(row["金额"]),
                        "category": row["分类"],
                        "note": row["备注"] if row["备注"] else None
                    }
                    
                    upd_url = f"{API_URL}/update"
                    resp = requests.post(upd_url, json=payload, headers={"X-API-Key": API_KEY}, timeout=10)
                    
                    if resp.status_code == 200:
                        update_count += 1
                    else:
                        st.error(f"更新失败 ID {safe_id}: {resp.text}")

                if update_count > 0:
                    st.success(f"已更新 {update_count} 条记录")
                    changes_made = True

            if changes_made:
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            elif delete_count == 0 and not has_edits:
                 st.info("未检测到修改，请先编辑或勾选删除。")

        except Exception as e:
            st.error(f"操作发生错误: {e}")
else:
    st.info("暂无数据。")

# ====== Danger Zone ======
st.divider()
with st.expander("🚨 危险操作区 (Danger Zone)"):
    st.warning("以下操作不可恢复，请谨慎使用。")
    
    confirm_clear = st.checkbox("我确认要清空所有数据 (Delete All Data)")
    
    if st.button("💣 立即清空所有数据", type="secondary"):
        if not confirm_clear:
            st.error("请先勾选确认框，防止误操作。")
        else:
            try:
                clear_url = f"{API_URL}/clear"
                resp = requests.post(clear_url, headers={"X-API-Key": API_KEY}, timeout=15)
                
                if resp.status_code == 200:
                    st.success("所有数据已清空。")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"清空失败: {resp.text}")
            except Exception as e:
                st.error(f"API 请求失败: {e}")
