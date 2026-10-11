"""ต่อ task ทั้งหมดเข้าด้วยกัน: fetch -> transform -> validate -> save
"""
import argparse
import logging

from .fetch_daily import fetch_daily
from .fetch_station import fetch_station
from .fetch_today import fetch_today
from .save import save_daily, save_station, save_today
from .transform import transform_daily, transform_station, transform_today
from .validate import validate_daily, validate_station, validate_today


def run_station():
    return save_station(validate_station(transform_station(fetch_station())))


def run_daily(year, month, station_ids=None):
    return save_daily(validate_daily(transform_daily(fetch_daily(year, month, station_ids))))


def run_today():
    return save_today(validate_today(transform_today(fetch_today())))

# date is here kub
def main():
    parser = argparse.ArgumentParser(description="ThaiWater rainfall pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("station")
    daily = sub.add_parser("daily")
    daily.add_argument("--year", type=int, required=True)
    daily.add_argument("--month", type=int, help="1-12; ไม่ใส่ = ทั้งปี")
    sub.add_parser("today")
    args = parser.parse_args()

    if args.command == "station":
        run_station()
    elif args.command == "daily":
        for month in [args.month] if args.month else range(1, 13):
            run_daily(args.year, month)
    else:
        run_today()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    main()
