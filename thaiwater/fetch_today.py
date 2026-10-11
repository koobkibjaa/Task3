"""Task: ดึงฝนล่าสุดของทุกสถานีจาก API rain_24h (เรียกครั้งเดียวได้ทุกสถานี)

rain_24h = ฝนสะสม 24 ชม. ล่าสุด นับถอยหลังจากเวลาที่สถานีส่งข้อมูลล่าสุด
rain_1h  = ฝน 1 ชม. ล่าสุด
"""
import logging
from datetime import datetime

from . import api, config, storage

log = logging.getLogger(__name__)


def fetch_today(run_time=None):
    """รันซ้ำได้ ไม่ทับรอบก่อน"""
    run_time = run_time or datetime.now()
    payload = api.get_json(config.TODAY_API)
    path = config.RAW_DIR / "today" / ("rain_24h_" + run_time.strftime("%Y-%m-%d_%H%M") + ".json")
    storage.write_json(path, payload)
    log.info("fetched %d stations -> %s", len(payload["data"]), path)
    return str(path)
