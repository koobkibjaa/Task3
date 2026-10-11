from datetime import datetime
from airflow.sdk import dag, task
import pendulum
from airflow.sdk import dag, task

#automatic
@dag(
    schedule="*/5 * * * *",
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Bangkok"),
    catchup=False,
    tags=["practice"],
)
def practice_dag():
    ...

#
@task
def make_report(temp, rain):
    import pandas as pd
    from datetime import datetime

    rows = []
    for city in temp:
        rows.append({
            "city": city,
            "temperature": temp[city],
            "rain": rain[city],
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    output = "/mnt/d/2026/Y4T1/Project/Task3/output/practice_report.csv"
    import os
    os.makedirs(os.path.dirname(output), exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False, encoding="utf-8-sig")
    print(f"บันทึกไฟล์แล้วที่ {output}")




#manual

@dag(schedule=None, start_date=datetime(2026, 10, 1), catchup=False, tags=["practice"])
def practice_dag():

    @task
    def get_temperature():
        print("กำลังดึงข้อมูลอุณหภูมิ...")
        return {"bangkok": 33, "chiangmai": 27}

    @task(retries=2)
    def get_rain():
        print("กำลังดึงข้อมูลฝน...")
        return {"bangkok": 12, "chiangmai": 5}
        
    @task
    def make_report(temp, rain):
        for city in temp:
            print(f"{city}: อุณหภูมิ {temp[city]}°C ฝน {rain[city]} มม.")

    make_report(get_temperature(), get_rain())


practice_dag()
