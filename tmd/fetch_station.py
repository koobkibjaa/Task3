"""Task: ดึงรายชื่อสถานี TMD จาก Station API แล้วเก็บ JSON ดิบ"""
import logging

from . import api, config, storage

log = logging.getLogger(__name__)


def fetch_station():
    payload = api.get_json(config.STATION_API)
    path = config.RAW_DIR / "station.json"
    storage.write_json(path, payload)
    log.info("fetched %d stations -> %s", len(payload["Station"]), path)
    return str(path)
