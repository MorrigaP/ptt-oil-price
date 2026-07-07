import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime, timezone, timedelta

URL = "https://oilprice.ryangl.com/en/"

# ===== map ชื่อจากเว็บ -> fuel_type มาตรฐานของเรา =====
NAME_TO_FUEL_TYPE = {
    "Diesel B20": "diesel_b20",
    "Diesel": "diesel",
    "Gasohol E20": "gasohol_e20",
    "Gasohol 91": "gasohol_91",
    "Gasohol 95": "gasohol_95",
    "Gasoline 95": "gasoline_95",
    "Premium Diesel": "premium_diesel",
    "Super Power GSH95": "superpower_gasohol_95",
}

resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# วันที่ดึงข้อมูล (เวลาไทย UTC+7)
capture_date = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")

# ===== หา table แล้วดึงแต่ละแถว =====
rows = []
warnings = []

table = soup.find("table")
if table is None:
    raise ValueError("ERROR: ไม่พบ table ในหน้าเว็บ - โครงสร้างอาจเปลี่ยน")

for tr in table.find_all("tr")[1:]:  # ข้าม header row
    cells = tr.find_all("td")
    if len(cells) < 2:
        continue

    fuel_cell = cells[0].get_text(strip=True)   # "Diesel B20      ดีเซล B20"
    price_today = cells[1].get_text(strip=True)  # "32.50"

    # แยกชื่ออังกฤษ (ตัวแรกก่อนภาษาไทย) - ใช้เทียบ mapping
    # เว็บวางชื่ออังกฤษ + ไทยติดกัน เลย match จาก key ที่รู้จัก
    matched_type = None
    matched_en = None
    for en_name, ftype in NAME_TO_FUEL_TYPE.items():
        if fuel_cell.startswith(en_name):
            matched_type = ftype
            matched_en = en_name
            break

    if matched_type is None:
        warnings.append(f"⚠️ UNKNOWN fuel: '{fuel_cell}' - please add to NAME_TO_FUEL_TYPE")
        matched_type = "unknown"
        matched_en = fuel_cell

    # ชื่อไทย = ส่วนที่เหลือหลังตัดชื่ออังกฤษออก
    name_th = fuel_cell.replace(matched_en, "").strip() if matched_en else fuel_cell

    # validate ราคาเป็นตัวเลข
    try:
        price_val = float(price_today)
    except ValueError:
        warnings.append(f"⚠️ INVALID price for '{fuel_cell}': '{price_today}' - skipped")
        continue

    rows.append({
        "capture_date": capture_date,
        "price_date_th": capture_date,  # เว็บนี้ไม่ให้วันที่ไทยแยก ใช้ capture_date แทน
        "company": "PTT",
        "fuel_type": matched_type,
        "fuel_name_th": name_th,
        "price": price_today,
    })

# ===== แจ้งเตือนถ้ามีปัญหา =====
if warnings:
    print("=" * 50)
    print("DATA QUALITY WARNINGS:")
    for w in warnings:
        print(w)
    print("=" * 50)

# ===== ต้องได้อย่างน้อย 5 แถว ไม่งั้นถือว่าผิดปกติ ไม่เขียนทับ =====
if len(rows) < 5:
    raise ValueError(f"ERROR: ได้แค่ {len(rows)} แถว (คาดว่าควรมี ~8) - หยุดไม่เขียน CSV เพื่อกันข้อมูลพัง")

# ===== เขียนลง CSV =====
csv_path = "oil_prices.csv"
file_exists = os.path.exists(csv_path)
fieldnames = ["capture_date", "price_date_th", "company", "fuel_type", "fuel_name_th", "price"]

with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows for {capture_date}")
for r in rows:
    print(f"  {r['fuel_type']}: {r['fuel_name_th']} = {r['price']}")
