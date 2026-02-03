# GTPinput
GPT智能记录日常开支
# GPT 记账系统（GPT → Make → Google Sheets → Streamlit）

这是一个由 GPT 驱动的个人记账与可视化系统，支持自然语言记账、自动分类、实时汇总，并通过 Streamlit 提供手机/电脑友好的可视化 Dashboard。

系统设计遵循「**数据层稳定、逻辑层可替换、展示层可演进**」的原则，适合长期使用与持续扩展。

---

## 一、系统能力概览

- ✅ 自然语言 / 语音记账（GPT）
- ✅ 自动结构化（日期 / 分类 / 金额 / 状态）
- ✅ 自动写入 Google Sheets（Make）
- ✅ 数据清洗与口径统一（Ledger_Clean）
- ✅ 月 / 年 / 分类自动汇总
- ✅ Streamlit Dashboard（趋势图 / 饼图 / KPI）
- ✅ 手机、电脑均可访问
- ✅ 完全免费方案（Streamlit Community Cloud）

---

## 二、整体架构

GPT（输入层）
↓
Make（执行层 / Webhook）
↓
Google Sheets（数据层）
├─ Ledger_Raw 原始记录（唯一写入点）
├─ Ledger_Clean 清洗与派生（公式）
├─ Summary_* 汇总视图
↓
Streamlit（展示层）


---

## 三、数据表结构

### 1️⃣ Ledger_Raw（原始数据表）
> Make 写入的唯一表，禁止手工公式

| 列名 | 说明 |
|---|---|
| 日期 | 允许 date 或文本 YYYY-MM-DD |
| 项目 | 消费内容 |
| 金额 | 数值 |
| 货币 | 如 CNY |
| 分类 | GPT 自动分类 |
| 备注 | 可选 |
| 记录来源 | GPT / 手动 |
| 创建时间 | ISO 时间 |
| 状态 | normal / pending / invalid |

---

### 2️⃣ Ledger_Clean（清洗表）
> 全部由公式生成，不手写数据

核心逻辑：
- 统一日期格式（兼容文本日期）
- 派生：年、月
- 是否有效：`status == normal`
- 有效金额：仅 normal 计入

---

### 3️⃣ Summary_*（汇总表）
- `Summary_Month`：按月汇总
- `Summary_Category`：按分类汇总
- `Summary_Year`：按年度汇总

全部使用 **Ledger_Clean** 作为唯一统计来源。

---

## 四、Streamlit Dashboard

- 数据源：`Ledger_Clean`
- 支持：
  - 本月 / 今年 KPI
  - 月度趋势折线图
  - 分类占比饼图（Donut）
  - 最近记录表
  - 月份 / 分类筛选
  - 手动刷新（30 秒缓存）

部署方式：
- GitHub Public Repo
- Streamlit Community Cloud
- `requirements.txt`：`streamlit`, `pandas`, `plotly`

---

## 五、刷新与实时性

- 使用 `@st.cache_data(ttl=30)`
- 提供「立即刷新」按钮
- 实时性：**几秒 ~ 30 秒**

---

## 六、删除 / 修改数据原则

- 删除测试数据：直接删除 `Ledger_Raw` 整行（安全）
- 排除记录：将 `状态` 改为 `invalid`
- 永不在 Ledger_Clean / Summary 中手动编辑数据

---

## 七、当前状态

- 系统已稳定运行
- 数据链路打通
- UI 已完成第一版
- 可进入功能增强阶段

