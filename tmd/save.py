"""Task: ย้าย CSV ที่ผ่าน validate แล้วจาก staging ไปเป็นไฟล์ผลลัพธ์
"""
import logging
from pathlib import Path

from . import config, storage

log = logging.getLogger(__name__)


def _publish(csv_path, dst):
    storage.copy_file(csv_path, dst)
    log.info("saved %s", dst)
    return str(dst)


def save_station(csv_path):
    return _publish(csv_path, config.STATION_FILE)


def save_daily(csv_path):
    return _publish(csv_path, config.DAILY_DIR / Path(csv_path).name)


def save_today(csv_path):
    return _publish(csv_path, config.TODAY_DIR / Path(csv_path).name)
