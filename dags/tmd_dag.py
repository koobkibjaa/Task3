import sys
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

# ให้ task import แพ็กเกจ thaiwater/ และ tmd/ ได้ แม้ไม่ได้ตั้ง PYTHONPATH (เช่นรัน airflow บนเครื่องตรง ๆ ไม่ผ่าน docker)
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

TZ = pendulum.timezone("Asia/Bangkok")
# ทุก task: ถ้า raise -> retry 2 ครั้ง ห่างกัน 5 นาที แล้วค่อยขึ้น failed
DEFAULT_ARGS = {"retries": 2, "retry_delay": pendulum.duration(minutes=5)}


def run_day(data_interval_end):
    """
    วันที่ของรอบนี้ (เวลาไทย): รอบตามตารางใช้ data_interval_end
    กด Trigger โดยไม่ใส่ logical date -> data_interval_end เป็น None -> ใช้เวลาปัจจุบัน
    """
    return (data_interval_end or pendulum.now(TZ)).in_timezone(TZ)


@dag(schedule="0 7 * * *", start_date=pendulum.datetime(2026, 1, 1, tz=TZ), catchup=False, default_args=DEFAULT_ARGS, tags=["tmd"])
def tmd_today():
    """
    ทุกวัน 07:00 (ผลตรวจอากาศ 07:00 พร้อมฝนสะสม 24 ชม.)
    ไฟล์ชื่อ tmd_today/<YYYY-MM-DD_HHMM>.csv -> trigger เองวันเดียวกันคนละเวลาไม่ทับกัน
    """

    @task
    def fetch():
        from tmd.fetch_today import fetch_today
        return fetch_today()

    @task
    def transform(raw_path):
        from tmd.transform import transform_today
        return transform_today(raw_path)

    @task
    def validate(csv_path):
        from tmd.validate import validate_today
        return validate_today(csv_path)

    @task
    def save(csv_path):
        from tmd.save import save_today
        return save_today(csv_path)

    save(validate(transform(fetch())))


@dag(schedule="0 8 * * *", start_date=pendulum.datetime(2026, 1, 1, tz=TZ), catchup=False, default_args=DEFAULT_ARGS, tags=["tmd"])
def tmd_daily():
    """
    ทุกวัน 08:00 ดึงข้อมูลรายวันตั้งแต่วันที่ 1 ของเดือน ถึง 2 วันก่อน (API รายวันออกช้า ~2 วัน)
    เหมือน thaiwater_daily: ดึงซ้ำทั้งเดือนทุกวัน save เขียนทับไฟล์รายวัน -> วันไหนเคยพัง/ข้อมูลออกช้า รอบถัดไปได้ใหม่เอง
    end = วันรัน - 2 วัน, start = วันที่ 1 ของเดือนเดียวกับ end (รันวันที่ 1-2 ของเดือน -> ได้เดือนก่อนครบทั้งเดือน)
    API ให้ทีละวัน -> 1 วัน = 1 mapped task (fetch[0], fetch[1], ...) วันไหนพังก็ retry แค่วันนั้น
    """

    @task
    def days(data_interval_end=None):
        end = run_day(data_interval_end).date() - pendulum.duration(days=2)
        return [end.replace(day=d).isoformat() for d in range(1, end.day + 1)]

    @task
    def fetch(day):
        from tmd.fetch_daily import fetch_daily
        return fetch_daily(day)

    @task
    def transform(raw_path):
        from tmd.transform import transform_daily
        return transform_daily(raw_path)

    @task
    def validate(csv_path):
        from tmd.validate import validate_daily
        return validate_daily(csv_path)

    @task
    def save(csv_path):
        from tmd.save import save_daily
        return save_daily(csv_path)

    raw = fetch.expand(day=days())
    save.expand(csv_path=validate.expand(csv_path=transform.expand(raw_path=raw)))


tmd_today()
tmd_daily()
