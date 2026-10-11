"""Task: ตรวจ CSV ใน staging ก่อน save

- ปัญหาโครงสร้าง (ไฟล์ว่าง, คอลัมน์หาย, แถวซ้ำ, วันที่ผิดรูปแบบ) -> raise ValidationError ให้ task fail
- ปัญหาค่าข้อมูล (พิกัดนอกประเทศไทย, ฝนติดลบ/สูงผิดปกติ) -> แค่ log warning เพราะเป็นข้อมูลจากต้นทาง
คืนค่า path เดิม เพื่อส่งต่อให้ task save
"""
import logging
from collections import Counter
from datetime import datetime

from . import config, storage

log = logging.getLogger(__name__)

# กรอบประเทศไทยแบบหยาบ ๆ
LAT_RANGE = (5.0, 21.0)    
LON_RANGE = (97.0, 106.0)
# mm ต่อวัน มากกว่านี้ถือว่าน่าสงสัย
MAX_RAIN_24H = 500.0        


class ValidationError(Exception):
    pass


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check_structure(rows, header, path):
    if not rows:
        raise ValidationError("%s: no rows" % path)
    missing = set(header) - set(rows[0])
    if missing:
        raise ValidationError("%s: missing columns %s" % (path, sorted(missing)))


def _check_unique(rows, keys, path):
    counts = Counter(tuple(row[k] for k in keys) for row in rows)
    dups = [k for k, n in counts.items() if n > 1]
    if dups:
        raise ValidationError("%s: %d duplicate %s, e.g. %s" % (path, len(dups), keys, dups[:5]))


def _check_dates(rows, column, fmt, path):
    bad = []
    for row in rows:
        try:
            datetime.strptime(row[column], fmt)
        except ValueError:
            bad.append(row[column])
    if bad:
        raise ValidationError("%s: %d bad %s values, e.g. %s" % (path, len(bad), column, bad[:5]))


def _warn_coords(rows, path):
    bad = []
    for row in rows:
        lat, lon = _to_float(row["lat"]), _to_float(row["lon"])
        if lat is None or lon is None or not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
            bad.append(row["station_id"])
    if bad:
        log.warning("%s: %d stations with lat/lon outside Thailand, e.g. %s", path, len(bad), bad[:5])


def _warn_rain(rows, column, path):
    blank = non_numeric = negative = too_high = 0
    for row in rows:
        if row[column] == "":
            blank += 1
            continue
        value = _to_float(row[column])
        if value is None:
            non_numeric += 1
        elif value < 0:
            negative += 1
        elif value > MAX_RAIN_24H:
            too_high += 1
    log.info("%s: %d rows, %d blank %s", path, len(rows), blank, column)
    if non_numeric or negative or too_high:
        log.warning("%s: %s non-numeric=%d negative=%d >%gmm=%d", path, column, non_numeric, negative, MAX_RAIN_24H, too_high)


def validate_station(csv_path):
    rows = storage.read_csv(csv_path)
    _check_structure(rows, config.STATION_HEADER, csv_path)
    _check_unique(rows, ["station_id"], csv_path)
    _warn_coords(rows, csv_path)
    log.info("%s: %d stations OK", csv_path, len(rows))
    return csv_path


def validate_daily(csv_path):
    rows = storage.read_csv(csv_path)
    _check_structure(rows, config.DAILY_HEADER, csv_path)
    _check_unique(rows, ["station_id", "date"], csv_path)
    _check_dates(rows, "date", "%Y-%m-%d", csv_path)
    _warn_rain(rows, "rain(mm)", csv_path)
    return csv_path


def validate_today(csv_path):
    rows = storage.read_csv(csv_path)
    _check_structure(rows, config.TODAY_HEADER, csv_path)
    _check_unique(rows, ["station_id"], csv_path)
    _check_dates(rows, "datetime", "%Y-%m-%d %H:%M", csv_path)
    _warn_coords(rows, csv_path)
    _warn_rain(rows, "rain_24h(mm)", csv_path)
    return csv_path
