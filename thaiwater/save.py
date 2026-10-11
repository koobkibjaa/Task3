"""Task: ย้าย CSV ที่ผ่าน validate แล้วจาก staging ไปเป็นไฟล์
"""
import logging
from collections import defaultdict
from pathlib import Path

from . import config, storage

log = logging.getLogger(__name__)


def save_station(csv_path):
    storage.copy_file(csv_path, config.STATION_FILE)
    log.info("saved %s", config.STATION_FILE)
    return str(config.STATION_FILE)


def save_daily(csv_path):
    by_date = defaultdict(dict)   # date -> {station_id: row}
    for row in storage.read_csv(csv_path):
        by_date[row["date"]][row["station_id"]] = [row[col] for col in config.DAILY_HEADER]

    paths = []
    for day, new_rows in sorted(by_date.items()):
        path = config.DAILY_DIR / (day + ".csv")
        rows = {}
        if path.exists():
            rows = {r["station_id"]: [r.get(col, "") for col in config.DAILY_HEADER] for r in storage.read_csv(path)}
        rows.update(new_rows)
        storage.write_csv(path, config.DAILY_HEADER, rows.values())
        paths.append(str(path))
    log.info("saved %d daily files to %s", len(paths), config.DAILY_DIR)
    return paths


def save_today(csv_path):
    path = config.TODAY_DIR / Path(csv_path).name
    storage.copy_file(csv_path, path)
    log.info("saved %s", path)
    return str(path)
