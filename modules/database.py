import sqlite3
import datetime
import os

DB_PATH = 'smartdoc_history.db'

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_date TEXT,
                filename TEXT,
                file_type TEXT,
                country TEXT,
                doc_id TEXT,
                expiry_date TEXT,
                drive_link TEXT,
                status TEXT,
                local_path TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_record(self, data):
        """
        添加一条归档记录
        data needs: filename, type, country, doc_id, expiry_date, drive_link, status
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        upload_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO history (upload_date, filename, file_type, country, doc_id, expiry_date, drive_link, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            upload_date,
            data.get('filename', 'Unknown'),
            data.get('type', 'OTHER'),
            data.get('country', 'N/A'),
            data.get('doc_id', 'N/A'),
            data.get('expiry_date', 'N/A'),
            data.get('drive_link', ''),
            data.get('status', 'Success')
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ [DB] Record saved: {data.get('filename')}")

    def get_recent_history(self, limit=20):
        """获取最近的历史记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "upload_date": row[1],
                "filename": row[2],
                "type": row[3],
                "country": row[4],
                "doc_id": row[5],
                "expiry_date": row[6],
                "drive_link": row[7],
                "status": row[8]
            })
        return results
