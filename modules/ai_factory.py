import openai
import base64
import json
import os
import fitz  # PyMuPDF

import streamlit as st

class AIProcessor:
    def __init__(self, settings_path='config/settings.json'):
        self.api_key = None
        
        # Priority 1: Streamlit Secrets (Cloud Environment)
        try:
            if "OPENAI_API_KEY" in st.secrets:
                self.api_key = st.secrets["OPENAI_API_KEY"]
                # Handle cases where user put it in [general] section
            if not self.api_key and "general" in st.secrets and "OPENAI_API_KEY" in st.secrets["general"]:
                 self.api_key = st.secrets["general"]["OPENAI_API_KEY"]
        except FileNotFoundError:
            pass # Secrets not found locally
            
        # Priority 2: Config File (Local Environment)
        if not self.api_key:
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key = config.get('openai_api_key')
            except:
                pass
        
        # Priority 3: Environment Variable
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
             print("⚠️ Warning: No OpenAI API Key found!")

        self.client = openai.OpenAI(api_key=self.api_key)

    def _pdf_to_image_base64(self, pdf_path):
        """将 PDF 第一页转为图片 Base64"""
        try:
            doc = fitz.open(pdf_path)
            if doc.page_count < 1: return None
            
            page = doc.load_page(0)
            # 2.0 倍清晰度，保证网页预览清晰
            mat = fitz.Matrix(2.0, 2.0) 
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # 转为 JPG
            return base64.b64encode(pix.tobytes("jpg")).decode('utf-8')
        except Exception as e:
            print(f"PDF 转图片失败: {e}")
            return None

    def analyze_image(self, file_path):
        base64_img = ""
        filename = os.path.basename(file_path).lower()
        
        # 1. 获取图片数据 (PDF转图 或 直接读取)
        if filename.endswith('.pdf'):
            print("正在转换 PDF 为预览图...")
            base64_img = self._pdf_to_image_base64(file_path)
            if not base64_img:
                return {"type": "ERROR", "name": "PDF读取失败", "expiry_date": "N/A"}
        else:
            with open(file_path, "rb") as img:
                base64_img = base64.b64encode(img.read()).decode('utf-8')

        # 2. 发给 AI
        system_prompt = """
        You are an expert global document OCR engine.
        Rules:
        1. Extract Name/ID in ORIGINAL language. For receipts, use Vendor Name as 'name'.
        2. Convert dates to 'YYYY-MM-DD'.
        3. Detect Country: 'CN', 'ES', 'US', or 'OTHER'.
        4. Fields: country, type (ID_CARD, PASSPORT, DRIVER_LICENSE, CONTRACT, INVOICE, OTHER), name, doc_id, expiry_date.
        5. EXTRACTION FOR EXPENSES: 
           - 'amount': Extract total amount as Number (e.g. 12.50).
           - 'category': Predict category (e.g. Food, Transport, Shopping).
        6. If unsure, put "N/A" for strings, 0 for numbers.
        Output pure JSON only.
        """

        try:
            print("正在请求 AI 分析...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "Extract JSON."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            content = response.choices[0].message.content
            print(f"AI 返回: {content}")
            
            result = json.loads(content)
            
            # ==========================================
            # ⭐ 核心修复点：把图片数据塞回给前端 ⭐
            # ==========================================
            result['preview_base64'] = base64_img 
            
            return result

        except Exception as e:
            print(f"AI Error: {e}")
            return {"type": "ERROR", "name": str(e)}