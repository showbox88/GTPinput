import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time

# --- Configuration ---
# GitHub Actions will provide these environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY environment variables not found.")
    print("Please set these in your GitHub Repository Secrets.")
    exit(1)

# Initialize Client
supabase: Client = create_client(url, key)

def get_recurring_rules():
    try:
        response = supabase.table("recurring_rules").select("*").eq("active", True).execute()
        return response.data
    except Exception as e:
        print(f"❌ Failed to fetch rules: {e}")
        return []

def main():
    print(f"🔄 Starting Recurring Expense Check at {datetime.now()}...")
    
    rules = get_recurring_rules()
    if not rules:
        print("ℹ️ No active recurring rules found.")
        return

    today = pd.Timestamp.today()
    current_day = today.day
    current_weekday = today.weekday() # 0=Mon
    current_month_str = today.strftime("%Y-%m")
    
    count_added = 0
    
    print(f"📅 Today: {today.strftime('%Y-%m-%d')} (Day {current_day}, Weekday {current_weekday})")

    for rule in rules:
        rule_name = rule.get("name")
        target_day = int(rule.get("day", 1))
        freq = rule.get("frequency", "Monthly")
        
        should_process = False
        start_date_check = ""
        end_date_check = ""

        print(f"🔍 Checking: {rule_name} (Freq: {freq}, Due: {target_day})...")

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
                 print(f"   ⏳ Skip (Weekly): Not reached day {target_day} yet.")

        else: # Default Monthly
            # Check period: Start of Month to End of Month
            start_date_check = f"{current_month_str}-01"
            last_day = pd.Timestamp(today.year, today.month, 1) + pd.offsets.MonthEnd(0)
            end_date_check = last_day.strftime("%Y-%m-%d")
            
            if current_day >= target_day:
                should_process = True
            else:
                 print(f"   ⏳ Skip (Monthly): Not reached day {target_day} yet.")
        
        # --- EXECUTION ---
        if should_process:
            try:
                res = supabase.table("expenses") \
                    .select("*") \
                    .eq("item", rule_name) \
                    .eq("category", rule["category"]) \
                    .eq("user_id", rule["user_id"]) \
                    .gte("date", start_date_check) \
                    .lte("date", end_date_check) \
                    .execute()
                
                if not res.data:
                    # Not found -> Insert
                    print(f"   👉 Due and not found. Creating record...")
                    
                    # Calculate Date
                    due_date = today
                    if freq == "Monthly":
                        try:
                            due_date = pd.Timestamp(year=today.year, month=today.month, day=target_day)
                        except ValueError:
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
                        "source": "github_action",
                        "user_id": rule["user_id"] 
                    }
                    
                    supabase.table("expenses").insert(payload).execute()
                    print(f"   ✅ Successfully added {rule_name}")
                    count_added += 1
                else:
                    print(f"   👌 Already recorded for this period.")
                    
            except Exception as e:
                print(f"   ❌ Error processing {rule_name}: {e}")

    print(f"\n✨ Completed! Added {count_added} new records.")

if __name__ == "__main__":
    main()
