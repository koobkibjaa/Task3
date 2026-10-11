"""Task: ดึงข้อมูลอากาศรายวันของทุกสถานี (ฝน, อุณหภูมิสูง/ต่ำสุด, ลมสูงสุด) ของ 1 วัน แล้วเก็บ JSON ดิบ
API นี้ออกข้อมูลช้า ~2 วัน ถ้าดึงวันนี้/เมื่อวานอาจยังไม่มีข้อมูล
"""
import logging
from datetime import date

from . import api, config, storage

log = logging.getLogger(__name__)


def fetch_daily(day):
    day_str = day.isoformat() if isinstance(day, date) else day
    payload = api.get_json(config.DAILY_API.replace("#date", day_str))
    path = config.RAW_DIR / "daily" / (day_str + ".json")
    storage.write_json(path, payload)
    log.info("fetched %d stations for %s -> %s", len(payload["items"]), day_str, path)
    return str(path)
