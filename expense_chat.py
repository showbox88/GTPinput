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
Your goal is to help the user manage expenses via natural language.

**CRITICAL INSTRUCTION**: You must **ALWAYS** reply in **Simplified Chinese (简体中文)**.

**Context Data**:
You have access to the user's recent expense records (provided below as JSON).
Use this data to answer questions or identify records to delete.

**Intents & Output Formats**:

1. **RECORD Expense** (User says "Lunch 20", "Taxi 50", "课本 55"):
   - **Rule**: If the user provides at least an "Item" and "Amount", output the JSON immediately. Do not ask for Date/Category unless explicitly ambiguous.
   - Defaults: Date = Today, Category = "General" (or infer from Item).
   - Output JSON: 
     ```json
     { "type": "record", "item": "...", "amount": 100, "category": "...", "date": "YYYY-MM-DD", "note": "..." }
     ```

2. **QUERY / ANSWER** (User says "Total spent on food?", "Last time I bought milk?"):
   - Analyze the provided Context Data.
   - Answer the user's question directly in PLAIN TEXT (friendly tone, Chinese).
   - Output JSON (wrapper):
     ```json
     { "type": "chat", "reply": "你在吃饭上花了 50 元..." }
     ```

3. **DELETE Expense** (User says "Delete the last taxi record", "Remove the 50 yuan expense"):
   - Find the single most likely matching record ID from the Context Data.
   - Output JSON:
     ```json
     { "type": "delete", "id": 12345, "reply": "已为你删除出租车费..." }
     ```

4. **UPDATE / MODIFY Expense** (User says "Change the 30 yuan one to 40", "Rename lunch to dinner"):
   - Find the matching record ID from Context Data.
   - Output JSON with "updates" object containing ONLY the changed fields.
   - Output JSON:
     ```json
     { 
       "type": "update", 
       "id": 12345, 
       "updates": { "amount": 40 }, 
       "reply": "已将金额修改为 40..." 
     }
     ```

**Current Date**: %TODAY%

**Context Data (Recent 50 records)**:
%DATA_CONTEXT%
"""

def process_user_message(user_text, df):
    """
    Process text input with Dataframe context.
    df: Pandas DataFrame containing ['id', 'date', 'item', 'amount', 'category', 'note']
    """
    client = get_openai_client()
    if not client:
        return {"type": "chat", "reply": "⚠️ OpenAI API Key missing."}

    # Prepare Data Context (Last 50 rows to save tokens)
    # Convert df to JSON string (records orientation)
    # Ensure df has standard columns
    context_str = "[]"
    if not df.empty:
        # Sort by date/id desc just in case
        df_sorted = df.sort_values(by="id", ascending=False).head(50)
        # Convert to simple list of dicts
        # Keep only relevant cols for context
        safe_cols = [c for c in ["id", "date", "item", "amount", "category", "note"] if c in df_sorted.columns]
        data_records = df_sorted[safe_cols].to_dict(orient="records")
        context_str = json.dumps(data_records, ensure_ascii=False)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    prompt = SYSTEM_PROMPT.replace("%TODAY%", today_str).replace("%DATA_CONTEXT%", context_str)

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
            # If valid JSON parsing fails, treat as normal chat
            return {"type": "chat", "reply": content}

    except Exception as e:
        return {"type": "chat", "reply": f"Error: {e}"}
