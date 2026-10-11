"""ต่อ task ทั้งหมดเข้าด้วยกัน: fetch -> transform -> validate -> save

รันจาก command line (ที่โฟลเดอร์โปรเจกต์):
    python -m tmd.pipeline station
    python -m tmd.pipeline daily --start 2026-01-01 --end 2026-01-31   (รวมวัน end)
    python -m tmd.pipeline today
"""
import argparse
import logging
from datetime import date, timedelta

from . import config
from .fetch_daily import fetch_daily
from .fetch_station import fetch_station
from .fetch_today import fetch_today
from .save import save_daily, save_station, save_today
from .transform import transform_daily, transform_station, transform_today
from .validate import validate_daily, validate_station, validate_today

log = logging.getLogger(__name__)


def daterange(start_date, end_date):
    # รวมวัน end_date ด้วย
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


def run_station():
    return save_station(validate_station(transform_station(fetch_station())))


def run_daily(day):
    if not config.STATION_FILE.exists():
        run_station()
    return save_daily(validate_daily(transform_daily(fetch_daily(day))))


def run_daily_range(start_date, end_date):
    #วันไหนพังก็ข้ามไปวันถัดไป แล้วค่อย raise ตอนจบถ้ามีวันที่พัง
    failed = []
    for day in daterange(start_date, end_date):
        try:
            run_daily(day)
        except Exception:
            log.exception("%s failed", day)
            failed.append(day.isoformat())
    if failed:
        raise RuntimeError("%d days failed: %s" % (len(failed), failed))


def run_today():
    return save_today(validate_today(transform_today(fetch_today())))


def main():
    parser = argparse.ArgumentParser(description="TMD weather pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("station")
    daily = sub.add_parser("daily")
    daily.add_argument("--start", type=date.fromisoformat, required=True)
    daily.add_argument("--end", type=date.fromisoformat, help="ไม่ใส่ = วันเดียวกับ start")
    sub.add_parser("today")
    args = parser.parse_args()

    if args.command == "station":
        run_station()
    elif args.command == "daily":
        run_daily_range(args.start, args.end or args.start)
    else:
        run_today()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()
