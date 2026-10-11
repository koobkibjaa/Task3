import sys
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

# ให้ task import แพ็กเกจ thaiwater/ และ tmd/ ได้ แม้ไม่ได้ตั้ง PYTHONPATH
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

TZ = pendulum.timezone("Asia/Bangkok")
# ทุก task: ถ้า raise -> retry 2 ครั้ง ห่างกัน 5 นาที แล้วค่อยขึ้น failed
DEFAULT_ARGS = {"retries": 2, "retry_delay": pendulum.duration(minutes=5)}


def run_day(data_interval_end):
    """วันที่ของรอบนี้ (เวลาไทย): รอบตามตารางใช้ data_interval_end
    กด Trigger โดยไม่ใส่ logical date -> data_interval_end เป็น None -> ใช้เวลาปัจจุบัน
    """
    return (data_interval_end or pendulum.now(TZ)).in_timezone(TZ)


@dag(schedule="0 7 * * *", start_date=pendulum.datetime(2026, 1, 1, tz=TZ), catchup=False, default_args=DEFAULT_ARGS, tags=["thaiwater"])
def thaiwater_today():
    """ทุกวัน 07:00 (เวลาตัดรอบฝนรายวันของ ThaiWater)"""

    @task
    def fetch():
        from thaiwater.fetch_today import fetch_today
        return fetch_today()

    @task
    def transform(raw_path):
        from thaiwater.transform import transform_today
        return transform_today(raw_path)

    @task
    def validate(csv_path):
        from thaiwater.validate import validate_today
        return validate_today(csv_path)

    @task
    def save(csv_path):
        from thaiwater.save import save_today
        return save_today(csv_path)

    save(validate(transform(fetch())))


@dag(schedule="30 7 * * *", start_date=pendulum.datetime(2026, 1, 1, tz=TZ), catchup=False, default_args=DEFAULT_ARGS, tags=["thaiwater"])
def thaiwater_daily():
    """ทุกวัน 07:30 ดึงฝนรายวันของเดือนปัจจุบันใหม่ทั้งเดือน
    save อัปเดตเขียนทับตามสถานี+วันที่ (มีแล้วทับ ยังไม่มีเพิ่ม) -> รันซ้ำ/retryได้ -> ไม่มีแถวซ้ำ
    """

    @task
    def fetch_station():
        from thaiwater.pipeline import run_station
        return run_station()

    @task(execution_timeout=pendulum.duration(hours=3))
    def fetch(data_interval_end=None):
        from thaiwater.fetch_daily import fetch_daily
        day = run_day(data_interval_end)
        return fetch_daily(day.year, day.month)

    @task
    def transform(raw_path):
        from thaiwater.transform import transform_daily
        return transform_daily(raw_path)

    @task
    def validate(csv_path):
        from thaiwater.validate import validate_daily
        return validate_daily(csv_path)

    @task
    def save(csv_path):
        from thaiwater.save import save_daily
        return save_daily(csv_path)

    raw = fetch()
    fetch_station() >> raw
    save(validate(transform(raw)))


thaiwater_today()
thaiwater_daily()
