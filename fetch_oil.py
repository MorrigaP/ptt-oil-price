import requests
import csv
import os
import json
from datetime import datetime, timezone, timedelta

# ===== ดึงราคาน้ำมันจาก Thai Oil API (REST/JSON) =====
API_URL = "https://api.chnwt.dev/thai-oil-api"

resp = requests.get(API_URL, timeout=30)
resp.raise_for_status()

# ===== DIAGNOSTIC: ดูว่า API คืนอะไรมากันแน่ =====
print("=== STATUS CODE ===")
print(resp.status_code)
print("=== RAW TEXT (first 1500 chars) ===")
print(resp.text[:1500])
print("=== END RAW ===")

data = resp.json()

# เช็คว่า data เป็น type อะไร
print(f"=== TYPE of data: {type(data)} ===")

# ถ้าเป็น string (JSON ซ้อน) ให้ parse อีกชั้น
if isinstance(data, str):
    print("=== data is STRING, parsing again ===")
    data = json.loads(data)
    print(f"=== TYPE after re-parse: {type(data)} ===")

# แสดง key ระดับบนสุด
if isinstance(data, dict):
    print(f"=== TOP-LEVEL KEYS: {list(data.keys())} ===")

# ===== หยุดไว้แค่นี้ก่อน เพื่อดู structure =====
# (ส่วนเขียน CSV จะเติมหลังเห็น structure จริง)
