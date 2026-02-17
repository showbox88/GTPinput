import pandas as pd
import streamlit as st
import datetime

# Categories constant (can be imported by UI)
CATEGORIES = ["餐饮", "日用品", "交通", "服饰", "医疗", "娱乐", "居住", "其他"]

def load_expenses(supabase, limit=500):
    """
    Loads expenses from Supabase.
    Returns a cleaned DataFrame.
    """
    try:
        # Supabase RLS automatically filters by user_id if set up correctly
        response = supabase.table("expenses").select("*").order("date", desc=True).order("id", desc=True).limit(limit).execute()
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
            allowed = set(CATEGORIES)
            df["分类"] = df["分类"].apply(lambda x: x if x in allowed else "其他")
            
        df["项目"] = df.get("item", "")
        df["备注"] = df.get("note", "")
        df["金额"] = df.get("amount", 0)
        df["来源"] = df.get("source", "")
        
        return df   
        
    except Exception as e:
        print(f"数据加载失败: {e}")
        return pd.DataFrame()

def add_expense(supabase, user_id, date, item, amount, category, note="", source="manual"):
    """
    Adds a single expense record.
    """
    try:
        payload = {
            "date": str(date),
            "item": item,
            "amount": float(amount),
            "category": category,
            "note": note,
            "source": source,
            "user_id": user_id
        }
        supabase.table("expenses").insert(payload).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def add_expenses_batch(supabase, payloads):
    """
    Adds multiple expense records.
    """
    try:
        if payloads:
            supabase.table("expenses").insert(payloads).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def delete_expense(supabase, expense_id):
    try:
        supabase.table("expenses").delete().eq("id", expense_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def update_expense(supabase, expense_id, updates):
    try:
        supabase.table("expenses").update(updates).eq("id", expense_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_budgets(supabase):
    try:
        response = supabase.table("budgets").select("*").execute()
        return response.data
    except:
        return []

def add_budget(supabase, user_id, name, category, amount, color, icon):
    try:
        payload = {
            "name": name, 
            "category": category, 
            "amount": float(amount), 
            "color": color, 
            "icon": icon,
            "user_id": user_id
        }
        supabase.table("budgets").insert(payload).execute()
        return True
    except Exception as e:
        print(f"添加失败: {e}")
        return False

def delete_budget(supabase, bid):
    try:
        supabase.table("budgets").delete().eq("id", bid).execute()
        return True
    except:
        return False

def update_budget(supabase, bid, updates):
    try:
        supabase.table("budgets").update(updates).eq("id", bid).execute()
        return True
    except:
        return False

def get_recurring_rules(supabase):
    try:
        response = supabase.table("recurring_rules").select("*").eq("active", True).execute()
        return response.data
    except:
        return []

def add_recurring(supabase, user_id, name, amount, category, frequency, start_date):
    """
    Adds a recurring rule.
    """
    day_val = start_date.day
    if frequency == "Weekly":
        day_val = start_date.weekday() # 0=Mon, 6=Sun
    
    payload = {
        "name": name,
        "amount": amount,
        "category": category,
        "frequency": frequency,
        "day": day_val,
        "active": True,
        "user_id": user_id
    }
    supabase.table("recurring_rules").insert(payload).execute()

def delete_recurring(supabase, rid):
    try:
        supabase.table("recurring_rules").delete().eq("id", rid).execute()
        return True
    except:
        return False

def update_recurring(supabase, rid, updates):
    try:
        supabase.table("recurring_rules").update(updates).eq("id", rid).execute()
        return True
    except:
        return False

def check_and_process_recurring(supabase, user_id):
    """
    Manually check if any recurring rules match today's date/weekday and add them if not already added this cycle.
    """
    try:
        rules = get_recurring_rules(supabase)
        if not rules:
            return "没有发现活跃的订阅规则。"
        
        today = pd.Timestamp.today()
        current_day = today.day
        current_weekday = today.weekday() # 0=Mon
        current_month_str = today.strftime("%Y-%m")
        
        count_added = 0
        details = []

        for rule in rules:
            rule_name = rule.get("name")
            target_day = int(rule.get("day", 1))
            freq = rule.get("frequency", "Monthly")
            
            should_process = False
            start_date_check = ""
            end_date_check = ""
            
            # --- LOGIC SELECTION ---
            if freq == "Weekly":
                # Check period: Monday of this week to Sunday of this week
                start_of_week = today - pd.Timedelta(days=today.weekday())
                end_of_week = start_of_week + pd.Timedelta(days=6)
                
                start_date_check = start_of_week.strftime("%Y-%m-%d")
                end_date_check = end_of_week.strftime("%Y-%m-%d")
                
                # If today's weekday >= target weekday, it might be due
                if current_weekday >= target_day:
                    should_process = True
                else:
                    details.append(f"⏳ 跳过 (未到周{target_day+1}): {rule_name}")

            elif freq == "Yearly":
                 pass # Not fully implemented

            else: # Default Monthly
                # Check period: Start of Month to End of Month
                start_date_check = f"{current_month_str}-01"
                last_day = pd.Timestamp(today.year, today.month, 1) + pd.offsets.MonthEnd(0)
                end_date_check = last_day.strftime("%Y-%m-%d")
                
                if current_day >= target_day:
                    should_process = True
                else:
                    details.append(f"⏳ 跳过 (未到{target_day}号): {rule_name}")
            
            # --- EXECUTION ---
            if should_process:
                # Check duplicates
                res = supabase.table("expenses") \
                    .select("*") \
                    .eq("item", rule_name) \
                    .eq("category", rule["category"]) \
                    .gte("date", start_date_check) \
                    .lte("date", end_date_check) \
                    .execute()
                
                if not res.data:
                    # Calculate due date
                    due_date = today # Default to today
                    
                    if freq == "Monthly":
                        try:
                            due_date = pd.Timestamp(year=today.year, month=today.month, day=target_day)
                        except: # Invalid day (e.g. 31 in Feb)
                            due_date = pd.Timestamp(year=today.year, month=today.month, day=1) + pd.offsets.MonthEnd(0)
                    elif freq == "Weekly":
                        start_of_week = today - pd.Timedelta(days=today.weekday())
                        due_date = start_of_week + pd.Timedelta(days=target_day)

                    payload = {
                        "date": due_date.strftime("%Y-%m-%d"),
                        "item": rule_name,
                        "amount": float(rule["amount"]),
                        "category": rule["category"],
                        "note": f"🔄 自动订阅 ({freq})",
                        "source": "recurring_rule",
                        "user_id": user_id
                    }
                    supabase.table("expenses").insert(payload).execute()
                    count_added += 1
                    details.append(f"✅ 添加成功: {rule_name}")
                else:
                    details.append(f"⏭️ 跳过 (本期已付): {rule_name}")
        
        if count_added > 0:
            return f"成功添加 {count_added} 笔订阅:\n" + "\n".join(details)
        else:
            debug_msg = "✅ 所有到期订阅已记录 (No new items).\n"
            return debug_msg

    except Exception as e:
        return f"检查失败: {e}"
