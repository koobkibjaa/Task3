"""Task: ดึงผลตรวจอากาศราย 3 ชม. ล่าสุดของทุกสถานี (Weather3Hours) แล้วเก็บ JSON ดิบ
API รายวันออกช้า ~2 วัน จึงใช้ Weather3Hours ซึ่งอัปเดตทุก 3 ชม. (1:00, 4:00, 7:00, ... 22:00) แทน
"""
import logging
from datetime import datetime

from . import api, config, storage

log = logging.getLogger(__name__)


def fetch_today(run_time=None):
    run_time = run_time or datetime.now()
    payload = api.get_json(config.TODAY_API)
    path = config.RAW_DIR / "today" / (run_time.strftime("%Y-%m-%d_%H%M") + ".json")
    storage.write_json(path, payload)
    log.info("fetched %d stations -> %s", len(payload["Stations"]["Station"]), path)
    return str(path)
