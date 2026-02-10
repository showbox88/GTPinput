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
    current_month_str = today.strftime("%Y-%m")
    count_added = 0
    
    print(f"📅 Today is Day {current_day} of {current_month_str}")

    for rule in rules:
        rule_name = rule.get("name")
        rule_day = rule.get("day", 1)
        
        print(f"🔍 Checking rule: {rule_name} (Due Day: {rule_day})...")

        # Logic: If today >= rule_day, it SHOULD have been paid this month.
        if current_day >= rule_day:
            # Check if already paid
            start_date = f"{current_month_str}-01"
            # Calculate accurate end of month
            last_day = pd.Timestamp(today.year, today.month, 1) + pd.offsets.MonthEnd(0)
            end_date = last_day.strftime("%Y-%m-%d")
            
            try:
                res = supabase.table("expenses") \
                    .select("*") \
                    .eq("item", rule["name"]) \
                    .eq("category", rule["category"]) \
                    .eq("user_id", rule["user_id"]) \
                    .gte("date", start_date) \
                    .lte("date", end_date) \
                    .execute()
                
                if not res.data:
                    # Not found -> Insert
                    print(f"   👉 Due and not found. Creating record...")
                    
                    # Calculate Date
                    try:
                        due_date = pd.Timestamp(year=today.year, month=today.month, day=rule_day)
                    except ValueError:
                         due_date = pd.Timestamp(year=today.year, month=today.month, day=1) + pd.offsets.MonthEnd(0)
                    
                    payload = {
                        "date": due_date.strftime("%Y-%m-%d"),
                        "item": rule["name"],
                        "amount": float(rule["amount"]),
                        "category": rule["category"],
                        "note": "自动通过订阅规则生成 (GitHub Action)",
                        "source": "github_action",
                        "user_id": rule["user_id"] # Use the user_id from the rule
                    }
                    
                    supabase.table("expenses").insert(payload).execute()
                    print(f"   ✅ Successfully added {rule_name}")
                    count_added += 1
                else:
                    print(f"   👌 Already recorded for this month.")
                    
            except Exception as e:
                print(f"   ❌ Error processing {rule_name}: {e}")
        else:
             print(f"   ⏳ Not due yet (Due: {rule_day}, Today: {current_day})")

    print(f"\n✨ Completed! Added {count_added} new records.")

if __name__ == "__main__":
    main()
