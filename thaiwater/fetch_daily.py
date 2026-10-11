"""Task: ดึงฝนรายวันของทุกสถานีใน 1 เดือน จาก API rain_monthly_graph แล้วเก็บ JSON ดิบ

API นี้ต้องเรียกทีละสถานี -> ~4,000 request ต่อเดือน ใช้เวลานาน
ฝนรายวัน = ฝนสะสม 07:00 ของวันนั้น ถึง 07:00 ของวันถัดไป
"""
import logging

import requests

from . import api, config, storage

log = logging.getLogger(__name__)


def fetch_daily(year, month, station_ids=None):
    if station_ids is None:
        station_ids = [row["station_id"] for row in storage.read_csv(config.STATION_FILE)]

    result = {}
    for i, station_id in enumerate(station_ids, 1):
        params = {"station_id": station_id, "month": month, "year": year}
        try:
            result[station_id] = api.get_json(config.DAILY_API, params=params)
        except (requests.RequestException, ValueError) as e:
            # log แล้ว raise ต่อ -> task fail -> Airflow retry หรือแจ้ง failed
            log.error("station %s failed: %s", station_id, e)
            raise
        if i % 200 == 0:
            log.info("%d/%d stations", i, len(station_ids))

    path = config.RAW_DIR / "daily" / ("%d-%02d.json" % (year, month))
    storage.write_json(path, result)
    log.info("fetched %d stations -> %s", len(result), path)
    return str(path)
