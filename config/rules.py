import datetime
import re

# =========================================================
# 📂 文件夹名称配置 (保持不变)
# =========================================================
FOLDER_MAP = {
    "PASSPORT":       "Passports",
    "ID_CARD":        "ID_Cards",
    "DRIVER_LICENSE": "Driver_Licenses",
    "CONTRACT":       "Contracts",
    "INVOICE":        "Invoices",
    "OTHER":          "Uncategorized"
}

# =========================================================
# 📝 智能命名规则 (已升级支持国家代码)
# =========================================================
def clean_str(s):
    if not s or s == "N/A": return "Unknown"
    s = re.sub(r'[\\/*?:"<>|]', '_', str(s))
    return s.strip()

def generate_filename(data):
    # 1. 准备数据
    country = data.get('country', 'OTHER')  # 新增：获取国家代码
    doc_type = data.get('type', 'OTHER')
    name = clean_str(data.get('name', 'Unknown'))
    doc_id = clean_str(data.get('doc_id', 'NoID'))
    expiry = clean_str(data.get('expiry_date', 'NoDate'))
    ext = data.get('extension', 'jpg')
    
    today = datetime.date.today().strftime("%Y%m%d")

    # 2. 如果国家是 OTHER 或 N/A，就不显示在文件名里，否则显示 [CN_Passport]
    if country in ['CN', 'ES', 'US']:
        prefix = f"[{country}_{doc_type}]"  # 例如: [CN_Passport]
    else:
        prefix = f"[{doc_type}]"            # 例如: [Passport]

    # 3. 组合文件名
    
    if doc_type == "PASSPORT":
        # [CN_Passport] ZhangSan_E123456_2028-01-01.jpg
        base_name = f"{prefix} {name}_{doc_id}_{expiry}"

    elif doc_type == "ID_CARD":
        # [ES_ID_CARD] Juan_12345X_2030-10-10.jpg
        base_name = f"{prefix} {name}_{doc_id}_{expiry}"

    elif doc_type == "DRIVER_LICENSE":
        base_name = f"{prefix} {name}_{expiry}"

    elif doc_type == "CONTRACT":
        # 合同通常不分国家，或者按日期排
        base_name = f"{expiry}_{prefix}_{name}"

    elif doc_type == "INVOICE":
        base_name = f"{today}_{prefix}_{name}"

    else:
        base_name = f"{prefix} {name}_{today}"

    return f"{base_name}.{ext}"