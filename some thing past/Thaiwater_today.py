
# dont forget to install the required libraries
'''
%pip install psycopg2
%pip install pandas
%pip install requests
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

# use for load station data
api_url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_yearly"   # new from website
station_file = "thaiwater_station.csv"

#for load station data and save to csv file
response = requests.get(api_url)
print("response status: %d" % response.status_code)
if (response.status_code == 200):

    response_json =response.json()
    data_list = response_json["data"]
    data_size = len(data_list)
    print("insert: %d" % data_size)
    # [note 2] บางสถานีมีตัวอักษรที่ tis-620 เขียนไม่ได้ (ภาษาลาว,   non-breaking space) -> UnicodeEncodeError
    #           เพิ่ม errors="replace" ให้ตัวที่เขียนไม่ได้กลายเป็น '?' แทนการ error
    # with open(station_file, 'w', encoding="tis-620", newline='') as file:   # old
    with open(station_file, 'w', encoding="tis-620", errors="replace", newline='') as file:   # new
        writer = csv.writer(file)
        header_row = ["station_id","station_name","lat","lon","agency_name","province","amphoe","tumbon"]
        writer.writerow(header_row)
        for dd in data_list:
            print (dd['station']['id'],dd['station']['tele_station_name']['th'])
            drow = [dd['station']['id'],dd['station']['tele_station_name']['th'],dd['station']['tele_station_lat'],dd['station']['tele_station_long'],dd['agency']['agency_name']['th'],dd['geocode']['province_name']['th'],dd['geocode']['amphoe_name']['th'],dd['geocode']['tumbon_name']['th']]
            
            writer.writerow(drow)


#load currently --> today data for each station yeah
# [note 5] new cell: ดึงฝน "ของวันนี้" ของทุกสถานี (ทั้ง cell นี้เป็นโค้ดใหม่)
#   - ใช้ API rain_24h: เรียกครั้งเดียวได้ทุกสถานี (~4,300 แห่ง) ใช้เวลาไม่กี่วินาที
#   - rain_24h = ฝนสะสม 24 ชั่วโมงล่าสุด นับถอยหลังจากเวลาที่สถานีส่งข้อมูลล่าสุด (คอลัมน์ datetime)
#   - วิธีใช้: รัน cell 1 (import) แล้วรัน cell นี้ได้เลย ไม่ต้องรัน cell 3, 4
#   - รันซ้ำเมื่อไหร่ก็ได้ จะได้ไฟล์ใหม่ตามเวลาที่รัน (ไม่ทับ ไม่ซ้ำ)
today_api_url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_24h"
os.makedirs("thaiwater_today", exist_ok=True)
now_str = datetime.now().strftime("%Y-%m-%d_%H%M")
today_file = "thaiwater_today/rain_24h_" + now_str + ".csv"

response = requests.get(today_api_url, timeout=60)
print("response status: %d" % response.status_code)
if (response.status_code == 200):
    data_list = response.json()["data"]
    print("stations: %d" % len(data_list))
    with open(today_file, 'w', encoding="tis-620", errors="replace", newline='') as file:
        writer = csv.writer(file)
        header_row = ["station_id","station_name","lat","lon","agency_name","province","amphoe","tumbon","datetime","rain_24h(mm)","rain_1h(mm)"]
        writer.writerow(header_row)
        for dd in data_list:
            drow = [dd['station']['id'],dd['station']['tele_station_name']['th'],dd['station']['tele_station_lat'],dd['station']['tele_station_long'],dd['agency']['agency_name']['th'],dd['geocode']['province_name']['th'],dd['geocode']['amphoe_name']['th'],dd['geocode']['tumbon_name']['th'],dd['rainfall_datetime'],dd.get('rain_24h'),dd.get('rain_1h')]
            writer.writerow(drow)
    print("saved:", today_file)