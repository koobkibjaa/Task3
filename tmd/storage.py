"""อ่าน/เขียนไฟล์ JSON และ CSV
ทุกฟังก์ชันเขียนทับไฟล์เดิม (ไม่ append) และเขียนลงไฟล์ .tmp ก่อนแล้วค่อย rename
"""
import csv
import json
import os
import shutil
from pathlib import Path

from . import config


def _tmp(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.with_name(path.name + ".tmp")


def write_json(path, data):
    tmp = _tmp(path)
    with open(tmp, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)
    os.replace(tmp, path)


def read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def write_csv(path, header, rows):
    # บางสถานีมีตัวอักษรที่ tis-620 เขียนไม่ได้ (ภาษาลาว, non-breaking space) -> errors="replace" ให้เป็น '?'
    tmp = _tmp(path)
    with open(tmp, "w", encoding=config.ENCODING, errors="replace", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)
    os.replace(tmp, path)


def read_csv(path):
    with open(path, encoding=config.ENCODING, newline="") as file:
        return list(csv.DictReader(file))


def copy_file(src, dst):
    tmp = _tmp(dst)
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)
