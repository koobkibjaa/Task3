"""Task: แปลง JSON ดิบ -> CSV ใน staging (ยังไม่ใช่ไฟล์ผลลัพธ์จนกว่าจะผ่าน validate)"""
import logging
from datetime import date
from pathlib import Path

from . import config, storage

log = logging.getLogger(__name__)


def _station_row(dd):
    station = dd["station"]
    geocode = dd["geocode"]
    return [
        station["id"],
        station["tele_station_name"]["th"],
        station["tele_station_lat"],
        station["tele_station_long"],
        dd["agency"]["agency_name"]["th"],
        geocode["province_name"]["th"],
        geocode["amphoe_name"]["th"],
        geocode["tumbon_name"]["th"],
    ]


def transform_station(raw_path):
    rows = [_station_row(dd) for dd in storage.read_json(raw_path)["data"]]
    path = config.STAGING_DIR / "station.csv"
    storage.write_csv(path, config.STATION_HEADER, rows)
    log.info("%d stations -> %s", len(rows), path)
    return str(path)


def transform_daily(raw_path, station_file=config.STATION_FILE):
    # รวมทุกสถานีทุกวันของเดือนไว้ในไฟล์ staging เดียว (save_daily จะแยกเป็นไฟล์รายวันเอง)
    stations = {row["station_id"]: row for row in storage.read_csv(station_file)}
    today = date.today().isoformat()

    rows = []
    for station_id, payload in storage.read_json(raw_path).items():
        station = stations.get(station_id)
        meta = [station[col] for col in config.STATION_HEADER] if station else [station_id] + [""] * 7
        for dd in payload.get("data") or []:
            # API ส่งวันในอนาคตของเดือนมาเป็นค่าว่างด้วย -> ไม่ต้องเก็บ
            if dd["rainfall_datetime"] > today:
                continue
            rows.append(meta + [dd["rainfall_datetime"], dd["rainfall_value"]])

    path = config.STAGING_DIR / "daily" / (Path(raw_path).stem + ".csv")
    storage.write_csv(path, config.DAILY_HEADER, rows)
    log.info("%d rows -> %s", len(rows), path)
    return str(path)


def transform_today(raw_path):
    rows = []
    for dd in storage.read_json(raw_path)["data"]:
        rows.append(_station_row(dd) + [dd["rainfall_datetime"], dd.get("rain_24h"), dd.get("rain_1h")])

    path = config.STAGING_DIR / "today" / (Path(raw_path).stem + ".csv")
    storage.write_csv(path, config.TODAY_HEADER, rows)
    log.info("%d stations -> %s", len(rows), path)
    return str(path)
