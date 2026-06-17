import requests
import csv
import os
from datetime import datetime, timezone, timedelta

# ===== ดึงราคาน้ำมันจาก API ทางการ PTT (SOAP/XML) =====
SOAP_URL = "https://orapiweb.pttor.com/oilservice/OilPrice.asmx"
SOAP_ACTION = "http://tempuri.org/CurrentOilPrice"

soap_body = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <CurrentOilPrice xmlns="http://tempuri.org/">
      <Language>thai</Language>
    </CurrentOilPrice>
  </soap:Body>
</soap:Envelope>"""

headers = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": SOAP_ACTION,
}

resp = requests.post(SOAP_URL, data=soap_body.encode("utf-8"), headers=headers, timeout=30)
resp.raise_for_status()

# ===== Parse XML response =====
import xml.etree.ElementTree as ET

# วันที่ดึงข้อมูล (เวลาไทย)
capture_date = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")

# พิมพ์ raw response ครั้งแรกไว้ debug (ดูใน Actions log)
print("=== RAW RESPONSE (first 2000 chars) ===")
print(resp.text[:2000])
print("=== END RAW ===")

# Parse — โครงสร้าง field จริงต้องดูจาก log รอบแรกแล้วปรับ
root = ET.fromstring(resp.text)

# เก็บทุก element ที่มีข้อความ เพื่อ map เป็นราคา
rows = []
ns = {}  # namespace จะเติมหลังเห็น log จริง

# วิธี generic: ไล่ทุก leaf node ที่มี text
for elem in root.iter():
    tag = elem.tag.split("}")[-1]  # ตัด namespace ออก
    text = (elem.text or "").strip()
    if text:
        rows.append({"capture_date": capture_date, "field": tag, "value": text})

# ===== เขียนลง CSV (append สะสม) =====
csv_path = "oil_prices.csv"
file_exists = os.path.exists(csv_path)

with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["capture_date", "field", "value"])
    if not file_exists:
        writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows for {capture_date}")
