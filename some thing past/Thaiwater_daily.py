
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


#load daily data for each station, loop in month
daily_api_url = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_monthly_graph?station_id=#id&month=#month&year=#year"
year = 2026
os.makedirs("thaiwater_daily", exist_ok=True)   # make directory if not exist   

with open(station_file, encoding="tis-620") as csv_file:   # new
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    next(csv_reader, None)  # skip the headers
    ii = 0
    for row in csv_reader:
        ii=ii+1
        station_id = row[0]
        print(ii, "Station:",station_id,row[1])
        for mm in range(1,13):
            api = daily_api_url.replace("#id",station_id).replace("#month",str(mm)).replace("#year",str(year))
            #print("month:",mm,api)
            #test_api = "http://localhost/thaiwater/rain_monthly.json"
            response = requests.get(api)
            #print("response status: %d" % response.status_code)
            if (response.status_code == 200):
                response_json =response.json()
                data_list = response_json["data"]
                data_size = len(data_list)
                #print("insert: %d" % data_size)
                for dd in data_list:
                    data_file = "thaiwater_daily/"+dd["rainfall_datetime"]+".csv"
                    need_header = False
                    if (not os.path.isfile(data_file)):
                        need_header = True
                                          
                    with open(data_file, 'a', encoding="tis-620", newline='') as file:
                        writer = csv.writer(file)
                        if (need_header):
                            header_row = ["station_id","station_name","lat","lon","agency_name","province","amphoe","tumbon","date","rain(mm)"]
                            writer.writerow(header_row)
                        drow = [station_id,row[1],row[2],row[3],row[4],row[5],row[6],row[7],dd["rainfall_datetime"],dd["rainfall_value"]]
                        writer.writerow(drow)

        