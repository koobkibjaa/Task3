
# dont forget to install the required libraries
'''
%pip install psycopg2
%pip install pandas
%pip install requests
%pip install truststore
'''
import psycopg2
import psycopg2.extras
import pandas as pd
import requests
import json
import time
from datetime import datetime
import csv
import os.path
from datetime import date, timedelta

# [note 7] www.tmd.go.th ส่ง certificate มาไม่ครบ (ขาด intermediate CA ของ GlobalSign)
#           -> requests ขึ้น SSLError: CERTIFICATE_VERIFY_FAILED ทุก request = สาเหตุที่รันไม่ได้
#           ใช้ truststore ให้ Python ตรวจ certificate ผ่าน Windows (เหมือน browser) ซึ่งไปดึง intermediate ที่ขาดมาเองได้
#           (ยังตรวจ SSL ตามปกติ ไม่ใช่การปิดด้วย verify=False)
import truststore   # new
truststore.inject_into_ssl() # new


# use for load station data
api_url = "https://data.tmd.go.th/api/Station/v1/?uid=api&ukey=api12345&format=json"   # new
station_file = "tmd_station.csv"   # new
out_dir = "tmd_daily"   # new
os.makedirs(out_dir, exist_ok=True)   # new


#for load station data and save to csv file
def text_or_blank(v):
    return v if isinstance(v, str) else ""

if (not os.path.isfile(station_file)):
    response = requests.get(api_url, timeout=60)
    print("response status: %d" % response.status_code)
    if (response.status_code == 200):
        data_list = response.json()["Station"]
        with open(station_file, 'w', encoding="tis-620", errors="replace", newline='') as file:
            writer = csv.writer(file)
            header_row = ["station_id","station_name_th","station_name_en","province","lat","lon"]
            writer.writerow(header_row)
            for dd in data_list:
                drow = [text_or_blank(dd["WmoCode"]),text_or_blank(dd["StationNameThai"]),text_or_blank(dd["StationNameEnglish"]),text_or_blank(dd["Province"]),text_or_blank(dd["Latitude"]),text_or_blank(dd["Longitude"])]
                writer.writerow(drow)
        print("saved:", station_file, len(data_list), "stations")
else:
    print("use existing:", station_file)

# [note 2] range() ไม่รวมตัวสุดท้าย 
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):   # new
        yield start_date + timedelta(n)

#tmd data for today

# [note 9] new: ดึงฝน "วันนี้" ของทุกสถานี TMD (ทำแบบเดียวกับ [note 6] ใน 02_Station_Thaiwater)
#   - API รายวัน (weather-station-daily) ออกช้า ~2 วัน -> ใช้ดึง "วันนี้" ไม่ได้
#     จึงใช้ Weather3Hours ซึ่งอัปเดตทุก 3 ชม. (1:00, 4:00, 7:00, ... 22:00) แทน
#   - rain(mm) = Rainfall24Hr = ฝนสะสม 24 ชม. ย้อนหลังจากเวลาที่วัด (ไม่ใช่ฝนตามวันปฏิทิน), rain_3hr(mm) = ฝนช่วง 3 ชม.ล่าสุด
#   - แต่ละสถานี: วันที่วัด = วันนี้ -> today | = เมื่อวาน -> yesterday | เก่ากว่านั้น -> ข้าม (สถานีไม่ส่งข้อมูล)
#   - ตัวเลขเก็บเป็นข้อความตามที่ API ส่งมา (API ส่งเป็น string อยู่แล้ว) + เก็บ JSON ดิบไว้ใน *_raw.json
#   - วิธีใช้: รัน cell 1 (import) และ cell 2 แล้วรัน cell นี้ ไม่ต้องรัน cell ดึงรายปี
today_str = datetime.now().strftime("%Y-%m-%d")
yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

rain_today_api_url = "https://data.tmd.go.th/api/Weather3Hours/V2/?uid=api&ukey=api12345&format=json"
os.makedirs("tmd_today", exist_ok=True)
today_file = "tmd_today/" + today_str + ".csv"
raw_file = "tmd_today/" + today_str + "_raw.json"

def text_or_blank(v):
    return v if isinstance(v, str) else ""   # API ส่งช่องที่ไม่มีค่าเป็น {}

response = requests.get(rain_today_api_url, timeout=60)
print("response status: %d" % response.status_code)
if (response.status_code == 200):
    data_list = response.json()["Stations"]["Station"]
    with open(raw_file, 'w', encoding="utf-8") as file:
        file.write(response.text)
    n_today = 0
    n_yesterday = 0
    n_skip = 0
    with open(today_file, 'w', encoding="tis-620", errors="replace", newline='') as file:
        writer = csv.writer(file)
        header_row = ["station_id","station_name_th","station_name_en","province","lat","lon","date","datetime","rain(mm)","rain_3hr(mm)","temp(c)","windDirection","windSpeed(km/h)","data_from"]
        writer.writerow(header_row)
        for dd in data_list:
            obs = dd["Observation"]
            obs_datetime = datetime.strptime(obs["DateTime"], "%m/%d/%Y %H:%M:%S")   # API ส่งมาแบบ 09/30/2026 04:00:00
            data_date = obs_datetime.strftime("%Y-%m-%d")
            if (data_date == today_str):
                data_from = "today"
                n_today = n_today + 1
            elif (data_date == yesterday_str):
                data_from = "yesterday"
                n_yesterday = n_yesterday + 1
            else:
                n_skip = n_skip + 1
                continue
            drow = [dd["WmoStationNumber"],text_or_blank(dd["StationNameThai"]),text_or_blank(dd["StationNameEnglish"]),text_or_blank(dd["Province"]),dd["Latitude"],dd["Longitude"],data_date,obs_datetime.strftime("%Y-%m-%d %H:%M:%S"),text_or_blank(obs.get("Rainfall24Hr")),text_or_blank(obs.get("Rainfall")),text_or_blank(obs.get("AirTemperature")),text_or_blank(obs.get("WindDirection")),text_or_blank(obs.get("WindSpeed")),data_from]
            writer.writerow(drow)
    print("today (%s): %d stations" % (today_str, n_today))
    print("yesterday (%s): %d stations" % (yesterday_str, n_yesterday))
    print("skip (older data): %d stations" % n_skip)
    print("saved:", today_file)