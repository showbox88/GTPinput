import openai
import json
import datetime
import streamlit as st
import pandas as pd

def get_openai_client():
    api_key = None
    try:
        with open("config/settings.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            api_key = config.get("openai_api_key")
    except:
        pass
    if not api_key:
        try:
            api_key = st.secrets["general"].get("OPENAI_API_KEY")
        except:
            pass
    if not api_key:
        return None
    return openai.OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
You are an intelligent financial assistant for 'GTPinput'.
Your goal is to help the user manage expenses, budgets, and subscriptions via natural language.

**CRITICAL INSTRUCTION**: You must **ALWAYS** reply in **Simplified Chinese (简体中文)**.

**Context Data**:
You have access to:
1. Recent Expenses (JSON)
2. Current Budgets (JSON)
3. Active Subscriptions (JSON)

**Intents & Output Formats**:

1. **RECORD Expense** (User says "Lunch 20", "买菜 30"):
   - Classify into: ["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "居住", "其他"].
   - Output JSON: 
     ```json
     { 
       "type": "record", 
       "records": [
         { "item": "Lunch", "amount": 20, "category": "餐饮", "date": "YYYY-MM-DD", "note": "..." }
       ]
     }
     ```

2. **QUERY / ANSWER** (User says "Total spent?", "How many subscriptions?"):
   - Answer directly in PLAIN TEXT.
   - Output JSON: `{ "type": "chat", "reply": "..." }`

3. **DELETE Expense** (User says "Delete the last taxi record"):
   - Output JSON: `{ "type": "delete", "id": 12345, "reply": "..." }`

4. **UPDATE Expense** (User says "Change 30 one to 40"):
   - Output JSON: `{ "type": "update", "id": 12345, "updates": { "amount": 40 }, "reply": "..." }`

5. **ADD BUDGET** (User says "Set dining budget to 2000", "Budget for Transport 500"):
   - Classify category strictly.
   - Output JSON:
     ```json
     {
       "type": "budget_add",
       "category": "餐饮",
       "amount": 2000,
       "reply": "已为您设置餐饮预算 2000。"
     }
     ```

6. **DELETE BUDGET** (User says "Remove dining budget"):
   - Find ID from Current Budgets.
   - Output JSON: `{ "type": "budget_delete", "id": 123, "reply": "..." }`

7. **ADD SUBSCRIPTION** (User says "Netflix monthly 15 dollars", "Gym weekly 200"):
   - Fields: `name`, `amount`, `category`, `frequency` (Monthly/Weekly/Yearly), `start_date` (YYYY-MM-DD, default today).
   - Output JSON:
     ```json
     {
       "type": "recurring_add",
       "name": "Netflix",
       "amount": 15,
       "category": "娱乐",
       "frequency": "Monthly",
       "start_date": "2023-10-01",
       "reply": "已添加 Netflix 月付订阅。"
     }
     ```

8. **DELETE SUBSCRIPTION** (User says "Cancel Netflix sub"):
   - Find ID from Active Subscriptions.
   - Output JSON: `{ "type": "recurring_delete", "id": 456, "reply": "..." }`

**Current Date**: %TODAY%

**Context Data**:
Expenses (Top 50): %DATA_EXPENSES%
Budgets: %DATA_BUDGETS%
Subscriptions: %DATA_SUBS%

User Currency Symbol: %USER_CURRENCY%

**CRITICAL CURRENCY INSTRUCTION**:
The user's preferred primary currency is "%USER_CURRENCY%". 
Whenever you generate a natural language `reply` that mentions an amount of money from their records, you MUST use ONLY the "%USER_CURRENCY%" symbol. Do NOT use words like "元", "dollars", "块", "yuan", "bucks", "USD", etc. 
Example Correct Reply: "已为您添加分类为餐饮的支出，金额为 %USER_CURRENCY%50。"
Example Incorrect Reply: "记录了 50 元餐饮费。"
EXCEPTION: If the user explicitly asks you to convert a value to another currency (e.g. "What is my spending in USD?"), you MUST calculate the approximate exchange rate using your internal knowledge (do not refuse by saying you cannot check live rates) and respond using the requested currency's symbol.
"""

def process_user_message(user_text, df, budgets=None, recurring=None, user_currency="$"):
    """
    Process text input with full context.
    """
    client = get_openai_client()
    if not client:
        return {"type": "chat", "reply": "⚠️ OpenAI API Key missing."}

    # 1. Expenses Context
    context_exp = "[]"
    if not df.empty:
        df_sorted = df.sort_values(by="id", ascending=False).head(50)
        safe_cols = [c for c in ["id", "date", "item", "amount", "category", "note"] if c in df_sorted.columns]
        context_exp = json.dumps(df_sorted[safe_cols].to_dict(orient="records"), ensure_ascii=False)

    # 2. Budgets Context
    context_bud = "[]"
    if budgets:
        # Simplify for specific matching
        b_simple = [{"id": b["id"], "category": b["category"], "amount": b["amount"]} for b in budgets]
        context_bud = json.dumps(b_simple, ensure_ascii=False)

    # 3. Recurring Context
    context_sub = "[]"
    if recurring:
        r_simple = [{"id": r["id"], "name": r["name"], "amount": r["amount"], "frequency": r["frequency"]} for r in recurring]
        context_sub = json.dumps(r_simple, ensure_ascii=False)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    prompt = SYSTEM_PROMPT \
        .replace("%TODAY%", today_str) \
        .replace("%DATA_EXPENSES%", context_exp) \
        .replace("%DATA_BUDGETS%", context_bud) \
        .replace("%DATA_SUBS%", context_sub) \
        .replace("%USER_CURRENCY%", user_currency)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content
        
        # Try to clean code blocks if present
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].strip()
        
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError:
            return {"type": "chat", "reply": content}

    except Exception as e:
        return {"type": "chat", "reply": f"Error: {e}"}
