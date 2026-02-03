# 系统结构与职责划分

本系统采用分层架构，每一层职责单一、可独立替换。

---

## 1. 输入层（GPT）

职责：
- 接收自然语言
- 提取结构化字段
- 不负责任何业务判断（如是否有效）

输出 JSON 示例：
{
  "date": "2026-02-02",
  "item": "午饭",
  "amount": 32,
  "currency": "CNY",
  "category": "餐饮",
  "status": "normal"
}

---

## 2. 执行层（Make）

职责：
- 接收 GPT Webhook
- 兜底逻辑（默认 status=normal）
- 写入 Google Sheets

约束：
- 只写 Ledger_Raw
- 不修改历史记录
- 不做统计

---

## 3. 数据层（Google Sheets）

### Ledger_Raw
- Source of Truth
- 允许删除行
- 不允许公式

### Ledger_Clean
- 全公式派生
- 数据标准化层
- 口径统一层

### Summary_*
- 聚合视图
- 仅读 Ledger_Clean

---

## 4. 展示层（Streamlit）

职责：
- 只读数据
- 不回写
- 不参与业务判断

特性：
- 可缓存
- 可部署
- 可扩展

---

## 5. 设计原则

- 单一写入点
- 数据向下流动
- 不反向依赖
- 删除不会破坏系统
- 任一层都可替换
