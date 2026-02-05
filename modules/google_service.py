import os
import json
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]

class GoogleService:
    def __init__(self, settings_path='config/settings.json'):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"配置文件读取失败: {e}")
            raise

        if not os.path.exists('credentials.json'):
            raise FileNotFoundError("未找到 credentials.json！")

        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    os.remove('token.json')
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.drive = build('drive', 'v3', credentials=creds)
        self.sheets = build('sheets', 'v4', credentials=creds)
        self.calendar = build('calendar', 'v3', credentials=creds)

    def find_or_create_folder(self, folder_name, parent_id):
        """
        核心升级：根据名字查找文件夹，如果没有就新建
        """
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_id}' in parents and trashed=false"
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            # 找到了，直接返回 ID
            print(f"✅ 找到文件夹: {folder_name}")
            return files[0]['id']
        else:
            # 没找到，新建一个
            print(f"📂 正在新建文件夹: {folder_name}")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            file = self.drive.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')

    def upload_file(self, local_path, filename, folder_name_hint):
        """
        folder_name_hint: 这里传入的是 rules.py 里的文件夹【名字】，不是 ID
        """
        try:
            # 1. 获取主目录 ID (从设置里读取)
            root_id = self.config['google']['drive_folder_id']
            
            # 2. 自动获取或创建目标子文件夹的 ID
            target_folder_id = self.find_or_create_folder(folder_name_hint, root_id)
            
            # 3. 上传文件到该 ID
            file_metadata = {
                'name': filename, 
                'parents': [target_folder_id]
            }
            
            media = MediaFileUpload(local_path, resumable=True)
            
            file = self.drive.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id, webViewLink'
            ).execute()
            
            print(f"文件上传成功: {filename}")
            return file.get('webViewLink')
            
        except Exception as e:
            print(f"Drive Upload Error: {e}")
            raise

    # ... 下面的 append_to_sheet 和 add_calendar_reminder 保持不变 ...
    def append_to_sheet(self, data):
        try:
            sheet_id = self.config['google']['sheet_id']
            body = {'values': [data]}
            self.sheets.spreadsheets().values().append(
                spreadsheetId=sheet_id, range="Sheet1!A:H",
                valueInputOption="USER_ENTERED", body=body
            ).execute()
        except Exception as e:
            print(f"Sheet Error: {e}")

    def add_calendar_reminder(self, title, expiry_date, days_before):
        if expiry_date == "N/A" or not days_before: return False
        try:
            exp_dt = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
            remind_dt = exp_dt - datetime.timedelta(days=int(days_before))
            event = {
                'summary': f"【证件到期】{title}",
                'description': f"您的证件即将于 {expiry_date} 到期。\n提醒设置：提前 {days_before} 天。",
                'start': {'date': remind_dt.strftime("%Y-%m-%d")},
                'end': {'date': (remind_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")},
                'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 9 * 60}]},
            }
            cal_id = self.config['google'].get('calendar_id', 'primary')
            self.calendar.events().insert(calendarId=cal_id, body=event).execute()
            return True
        except Exception as e:
            print(f"Calendar Error: {e}")
            return False