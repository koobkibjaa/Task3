"""ค่าคงที่ของ TMD (กรมอุตุนิยมวิทยา): URL ของ API, path ไฟล์, หัวคอลัมน์ CSV"""
import os
from pathlib import Path

# โฟลเดอร์หลักที่เก็บข้อมูล (default = โฟลเดอร์โปรเจกต์) เปลี่ยนได้ด้วย env RAIN_DATA_DIR
BASE_DIR = Path(os.environ.get("RAIN_DATA_DIR", Path(__file__).resolve().parent.parent))

RAW_DIR = BASE_DIR / "data" / "raw" / "tmd"          # JSON ดิบจาก API (ผลของ fetch)
STAGING_DIR = BASE_DIR / "data" / "staging" / "tmd"  # CSV ที่แปลงแล้ว รอ validate

# ไฟล์ผลลัพธ์สุดท้าย (ที่เดิมกับ notebook)
STATION_FILE = BASE_DIR / "tmd_station.csv"
DAILY_DIR = BASE_DIR / "tmd_daily"
TODAY_DIR = BASE_DIR / "tmd_today"

STATION_API = "https://data.tmd.go.th/api/Station/v1/?uid=api&ukey=api12345&format=json"
# ใส่ #date แทนวันที่ (เขียน URL เองเพราะ API ต้องการช่องว่างเป็น %20 ไม่ใช่ +)
DAILY_API = "https://www.tmd.go.th/api/WeatherObservationDailyStation/weather-station-daily?DateTime=#date%2017:00&Culture=th-TH"
TODAY_API = "https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345&format=json"

ENCODING = "tis-620"
TIMEOUT = 60

STATION_HEADER = ["station_id", "station_name_th", "station_name_en", "province", "lat", "lon"]
DAILY_HEADER = STATION_HEADER + ["date", "rain(mm)", "maxTemp(c)", "minTemp(c)", "maxWindDirection", "maxWindSpeed(km/h)"]
TODAY_HEADER = STATION_HEADER + ["date", "datetime", "rain(mm)", "rain_3hr(mm)", "temp(c)", "windDirection", "windSpeed(km/h)", "data_from"]
