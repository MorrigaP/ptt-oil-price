import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime, timezone, timedelta

URL = "https://oilprice.ryangl.com/en/"

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

# ===== แปลงวันที่เป็นภาษาไทย พ.ศ. (ให้ตรงกับข้อมูลเก่า) =====
THAI_MONTHS = {
    1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
    5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
    9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม",
}

def to_thai_date(dt):
    """แปลง datetime -> '7 กรกฎาคม 2569' (พ.ศ.)"""
    day = dt.day
    month_th = THAI_MONTHS[dt.month]
    year_be = dt.year + 543  # ค.ศ. -> พ.ศ.
    return f"{day} {month_th} {year_be}"

resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# วันที่ปัจจุบัน (เวลาไทย)
now_th = datetime.now(timezone(timedelta(hours=7)))
capture_date = now_th.strftime("%Y-%m-%d")
price_date_th = to_thai_date(now_th)   # ← format ไทย พ.ศ. เหมือนข้อมูลเก่า

rows = []
warnings = []

table = soup.find("table")
if table is None:
    raise ValueError("ERROR: ไม่พบ table ในหน้าเว็บ - โครงสร้างอาจเปลี่ยน")

for tr in table.find_all("tr")[1:]:
    cells = tr.find_all("td")
    if len(cells) < 2:
        continue

    fuel_cell = cells[0].get_text(strip=True)
    price_today = cells[1].get_text(strip=True)

    matched_type = None
    matched_en = None
    for en_name, ftype in NAME_TO_FUEL_TYPE.items():
        if fuel_cell.startswith(en_name):
            matched_type = ftype
            matched_en = en_name
            break

    if matched_type is None:
        warnings.append(f"⚠️ UNKNOWN fuel: '{fuel_cell}'")
        matched_type = "unknown"
        matched_en = fuel_cell

    name_th = fuel_cell.replace(matched_en, "").strip() if matched_en else fuel_cell

    try:
        price_val = float(price_today)
    except ValueError:
        warnings.append(f"⚠️ INVALID price for '{fuel_cell}': '{price_today}' - skipped")
        continue

    rows.append({
        "capture_date": capture_date,
        "price_date_th": price_date_th,   # ← ใช้ format ไทยแล้ว
        "company": "PTT",
        "fuel_type": matched_type,
        "fuel_name_th": name_th,
        "price": price_today,
    })

if warnings:
    print("=" * 50)
    print("DATA QUALITY WARNINGS:")
    for w in warnings:
        print(w)
    print("=" * 50)

if len(rows) < 5:
    raise ValueError(f"ERROR: ได้แค่ {len(rows)} แถว - หยุดไม่เขียน CSV")

csv_path = "oil_prices.csv"
file_exists = os.path.exists(csv_path)
fieldnames = ["capture_date", "price_date_th", "company", "fuel_type", "fuel_name_th", "price"]

with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows for {capture_date} ({price_date_th})")
for r in rows:
    print(f"  {r['fuel_type']}: {r['fuel_name_th']} = {r['price']}")
