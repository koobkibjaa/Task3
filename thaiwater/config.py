
import os
from pathlib import Path

# โฟลเดอร์หลักที่เก็บข้อมูล (default = โฟลเดอร์โปรเจกต์) เปลี่ยนได้ด้วย env RAIN_DATA_DIR
BASE_DIR = Path(os.environ.get("RAIN_DATA_DIR", Path(__file__).resolve().parent.parent))

RAW_DIR = BASE_DIR / "data" / "raw" / "thaiwater"# JSON ดิบจาก API (ผลของ fetch)
STAGING_DIR = BASE_DIR / "data" / "staging" / "thaiwater"# CSV ที่แปลงแล้ว รอ validate

# ไฟล์ผลลัพธ์สุดท้าย (ที่เดิมกับ notebook)
STATION_FILE = BASE_DIR / "thaiwater_station.csv"
DAILY_DIR = BASE_DIR / "thaiwater_daily"
TODAY_DIR = BASE_DIR / "thaiwater_today"

STATION_API = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_yearly"
DAILY_API = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_monthly_graph"
TODAY_API = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_24h"

ENCODING = "tis-620"
TIMEOUT = 60

STATION_HEADER = ["station_id", "station_name", "lat", "lon", "agency_name", "province", "amphoe", "tumbon"]
DAILY_HEADER = STATION_HEADER + ["date", "rain(mm)"]
TODAY_HEADER = STATION_HEADER + ["datetime", "rain_24h(mm)", "rain_1h(mm)"]
