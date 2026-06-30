import requests
import csv
import os
from datetime import datetime, timezone, timedelta

API_URL = "https://api.chnwt.dev/thai-oil-api/latest"

# ===== Map จากชื่อไทย -> รหัส fuel_type มาตรฐานของเราเอง =====
# (เพราะชื่อไทย+ราคามาเป็นคู่กันเสมอ ส่วน key อังกฤษจาก API ไม่น่าเชื่อถือ)
NAME_TO_FUEL_TYPE = {
    "เบนซิน 95": "gasoline_95",
    "แก๊สโซฮอล์ 95": "gasohol_95",
    "แก๊สโซฮอล์ 91": "gasohol_91",
    "แก๊สโซฮอล์ E20": "gasohol_e20",
    "แก๊สโซฮอล์ E85": "gasohol_e85",
    "ดีเซล": "diesel",
    "ดีเซล B7": "diesel",        
    "ดีเซล B20": "diesel_b20",
    "ดีเซลพรีเมียม": "premium_diesel",
    "ซูเปอร์พาวเวอร์ แก๊สโซฮอล์ 95": "superpower_gasohol_95",
    "แก๊ส NGV": "ngv",
}

resp = requests.get(API_URL, timeout=30)
resp.raise_for_status()
data = resp.json()

if not isinstance(data.get("response"), dict):
    print(f"ERROR: unexpected response: {resp.text[:500]}")
    raise ValueError("API response structure changed")

capture_date = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")
price_date_th = data["response"]["date"]
ptt = data["response"]["stations"]["ptt"]

rows = []
for original_key, info in ptt.items():
    name_th = info["name"]
    price = info["price"]

    # ใช้ name (ไทย) เป็นตัวตั้งหา fuel_type มาตรฐาน ไม่เชื่อ key จาก API
    fuel_type = NAME_TO_FUEL_TYPE.get(name_th)

    if fuel_type is None:
        print(f"⚠️ UNKNOWN name '{name_th}' (original key: '{original_key}') — please add to NAME_TO_FUEL_TYPE")
        fuel_type = f"unknown_{original_key}"  # กันตกหาย แต่ flag ไว้ให้เห็น

    rows.append({
        "capture_date": capture_date,
        "price_date_th": price_date_th,
        "company": "PTT",
        "fuel_type": fuel_type,
        "fuel_name_th": name_th,
        "price": price,
    })

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
    print(f"  {r['fuel_type']}: {r['fuel_name_th']} = {r['price']}")
