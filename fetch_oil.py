import requests
import csv
import os
from datetime import datetime, timezone, timedelta

# ===== ดึงราคาน้ำมันจาก Thai Oil API (REST/JSON) =====
API_URL = "https://api.chnwt.dev/thai-oil-api/latest"   # <-- เพิ่ม /latest

resp = requests.get(API_URL, timeout=30)
resp.raise_for_status()
data = resp.json()

# เช็คว่าได้โครงสร้างที่ถูกต้อง
if not isinstance(data.get("response"), dict):
    print(f"ERROR: unexpected response: {resp.text[:500]}")
    raise ValueError("API response structure changed")

# วันที่ดึงข้อมูล (เวลาไทย UTC+7)
capture_date = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")

# วันที่ที่ API ระบุ (ภาษาไทย พ.ศ.)
price_date_th = data["response"]["date"]

# ราคาน้ำมัน PTT แยกตามประเภท
ptt = data["response"]["stations"]["ptt"]

# ===== แตกเป็นแถว: หนึ่งประเภทน้ำมัน = หนึ่งแถว =====
rows = []
for fuel_type, info in ptt.items():
    rows.append({
        "capture_date": capture_date,
        "price_date_th": price_date_th,
        "company": "PTT",
        "fuel_type": fuel_type,
        "fuel_name_th": info["name"],
        "price": info["price"],
    })

# ===== เขียนลง CSV (append สะสมทุกวัน) =====
csv_path = "oil_prices.csv"
file_exists = os.path.exists(csv_path)
fieldnames = ["capture_date", "price_date_th", "company", "fuel_type", "fuel_name_th", "price"]

with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows for {capture_date} (price date: {price_date_th})")
for r in rows:
    print(f"  {r['fuel_type']}: {r['price']}")
