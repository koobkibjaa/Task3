
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

#tmd data for daily

#daily_api_url = "http://localhost/tmd/rain_daily.json?DateTime=#date%2017:00&Culture=th-TH"
daily_api_url = "https://www.tmd.go.th/api/WeatherObservationDailyStation/weather-station-daily?DateTime=#date%2017:00&Culture=th-TH"
# [note 10] station_id บางสถานีว่าง -> pandas อ่านทั้งคอลัมน์เป็น float -> ได้ 48380.0 แทน 48380 -> บังคับให้อ่านเป็นข้อความ
# df = pd.read_csv(station_file, encoding = 'tis-620')   # old
df = pd.read_csv(station_file, encoding = 'tis-620', dtype={'station_id': str})   # new
sel_df = df.loc[df['station_name_th'] == 'สมุทรปราการ สกษ.'].iloc[0]
print(sel_df['station_id'],sel_df['station_name_th'],sel_df['station_name_en'],sel_df['lat'],sel_df['lon'])

#specify date
start_date = date(2026, 1, 1) #Add your start date here
end_date = date(2026, 12, 31)
unmatched = set()   # [note 6] new: เก็บชื่อสถานีที่หาใน tmd_station.csv ไม่เจอ
for single_date in daterange(start_date, end_date):
    cur_date = single_date.strftime("%Y-%m-%d")
    print(single_date.strftime("%Y-%m-%d"))
    api = daily_api_url.replace("#date",cur_date)
    print(api)

    # response = requests.get(api)   # old
    try:   # new
        response = requests.get(api, timeout=60)
    except requests.exceptions.RequestException as e:
        print("request failed:", cur_date, e)
        continue
    if (response.status_code == 200):
        response_json =response.json()
        data_list = response_json["items"]
        data_size = len(data_list)

        # data_file = "D:/PhD-Semester-2/Code-Download/loadTMDStation_clean/tmd_daily_all_2024/tmd_"+cur_date+".csv"   # old
        data_file = out_dir + "/tmd_" + cur_date + ".csv"   # new


        # with open(data_file, 'a', encoding="tis-620", newline='') as file:   # old 
        with open(data_file, 'w', encoding="tis-620", errors="replace", newline='') as file:   # new
            writer = csv.writer(file)
            header_row = ["station_id","station_name_th","station_name_en","province","lat","lon","date","rain(mm)","maxTemp(c)","minTemp(c)","maxWindDirection","maxWindSpeed(km/h)"]
            writer.writerow(header_row)
            for dd in data_list:
                # [note 6] เดิม .iloc[0] บนผลลัพธ์ว่าง (ชื่อจาก API ไม่ตรงกับ csv) -> IndexError หยุดทั้ง loop
                #           เช็กก่อน ถ้าไม่เจอ: ยังเขียนข้อมูลอากาศไว้ (ใช้ stationId/ชื่อจาก API, ช่องอื่นว่าง) และจดชื่อไว้ใน unmatched
                # sel_df = df.loc[df['station_name_th'] == dd["stationName"]].iloc[0]   # old
                match = df.loc[df['station_name_th'] == dd["stationName"]]   # new
                if (match.empty):
                    unmatched.add(dd["stationName"])
                    drow = [dd["stationId"],dd["stationName"],"","","","",cur_date,dd["rainfall"],dd["maxTemperature"],dd["minTemperature"],dd["maxWindDirection"],dd["maxWindSpeed"]]
                else:
                    sel_df = match.iloc[0]
                    drow = [sel_df['station_id'],sel_df['station_name_th'],sel_df['station_name_en'],sel_df['province'],sel_df['lat'],sel_df['lon'],cur_date,dd["rainfall"],dd["maxTemperature"],dd["minTemperature"],dd["maxWindDirection"],dd["maxWindSpeed"]]
                writer.writerow(drow)
    else:
        print(response.status_code)

print("stations not found in", station_file, ":", len(unmatched))   # [note 6] new
for name in sorted(unmatched):
    print("  ", name)