"""Task: แปลง JSON ดิบ -> CSV ใน staging (ยังไม่ใช่ไฟล์ผลลัพธ์จนกว่าจะผ่าน validate)"""
import logging
from datetime import datetime, timedelta
from pathlib import Path

from . import config, storage

log = logging.getLogger(__name__)


def text_or_blank(v):
    return v if isinstance(v, str) else "" # API ส่งช่องที่ไม่มีค่าเป็น {}


def transform_station(raw_path):
    rows = []
    for dd in storage.read_json(raw_path)["Station"]:
        rows.append([
            text_or_blank(dd["WmoCode"]),
            text_or_blank(dd["StationNameThai"]),
            text_or_blank(dd["StationNameEnglish"]),
            text_or_blank(dd["Province"]),
            text_or_blank(dd["Latitude"]),
            text_or_blank(dd["Longitude"]),
        ])
    path = config.STAGING_DIR / "station.csv"
    storage.write_csv(path, config.STATION_HEADER, rows)
    log.info("%d stations -> %s", len(rows), path)
    return str(path)


def transform_daily(raw_path, station_file=config.STATION_FILE):
    """
    จับคู่สถานีจาก API กับ tmd_station.csv ด้วยชื่อภาษาไทย
    ถ้าหาชื่อไม่เจอ ยังเก็บข้อมูลอากาศไว้ (ใช้ stationId/ชื่อจาก API, ช่องอื่นว่าง) แล้ว log ชื่อไว้
    """
    stations = {}
    for row in storage.read_csv(station_file):
        stations.setdefault(row["station_name_th"], row) # ชื่อซ้ำ -> ใช้ตัวแรก 

    day = Path(raw_path).stem
    rows = []
    unmatched = set()
    for dd in storage.read_json(raw_path)["items"]:
        station = stations.get(dd["stationName"])
        if station:
            meta = [station[col] for col in config.STATION_HEADER]
        else:
            unmatched.add(dd["stationName"])
            meta = [dd.get("stationId"), dd["stationName"], "", "", "", ""]
        rows.append(meta + [day, dd.get("rainfall"), dd.get("maxTemperature"), dd.get("minTemperature"),
                            dd.get("maxWindDirection"), dd.get("maxWindSpeed")])

    if unmatched:
        log.warning("%s: %d stations not found in %s: %s", day, len(unmatched), station_file, sorted(unmatched))

    path = config.STAGING_DIR / "daily" / ("tmd_" + day + ".csv")
    storage.write_csv(path, config.DAILY_HEADER, rows)
    log.info("%d rows -> %s", len(rows), path)
    return str(path)


def transform_today(raw_path):
    """
    แต่ละสถานี: วันที่วัด = วันที่รัน -> today | = เมื่อวาน -> yesterday | เก่ากว่านั้น -> ข้าม
    rain(mm) = Rainfall24Hr = ฝนสะสม 24 ชม. ย้อนหลังจากเวลาที่วัด, rain_3hr(mm) = ฝนช่วง 3 ชม. ล่าสุด
    """
    run_date = datetime.strptime(Path(raw_path).stem, "%Y-%m-%d_%H%M").date()
    today_str = run_date.isoformat()
    yesterday_str = (run_date - timedelta(days=1)).isoformat()

    rows = []
    n_skip = 0
    for dd in storage.read_json(raw_path)["Stations"]["Station"]:
        obs = dd["Observation"]
        obs_datetime = datetime.strptime(obs["DateTime"], "%m/%d/%Y %H:%M:%S")   # API ส่งมาแบบ 09/30/2026 04:00:00
        data_date = obs_datetime.strftime("%Y-%m-%d")
        if data_date == today_str:
            data_from = "today"
        elif data_date == yesterday_str:
            data_from = "yesterday"
        else:
            n_skip += 1
            continue
        rows.append([
            dd["WmoStationNumber"],
            text_or_blank(dd["StationNameThai"]),
            text_or_blank(dd["StationNameEnglish"]),
            text_or_blank(dd["Province"]),
            dd["Latitude"],
            dd["Longitude"],
            data_date,
            obs_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            text_or_blank(obs.get("Rainfall24Hr")),
            text_or_blank(obs.get("Rainfall")),
            text_or_blank(obs.get("AirTemperature")),
            text_or_blank(obs.get("WindDirection")),
            text_or_blank(obs.get("WindSpeed")),
            data_from,
        ])

    path = config.STAGING_DIR / "today" / (Path(raw_path).stem + ".csv")
    storage.write_csv(path, config.TODAY_HEADER, rows)
    log.info("%d stations (skip %d with older data) -> %s", len(rows), n_skip, path)
    return str(path)
