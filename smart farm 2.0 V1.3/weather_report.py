import os
import json
from datetime import datetime
from main import latest_data  # ดึงข้อมูลล่าสุดจาก main.py

LOG_DIR = "log"
DAY_FILE = os.path.join(LOG_DIR, "day.json")
NIGHT_FILE = os.path.join(LOG_DIR, "night.json")
TEMP_LOG_FILE = os.path.join(LOG_DIR, "temp_log_in_day.txt")

os.makedirs(LOG_DIR, exist_ok=True)

def append_temp_to_json():
    if latest_data["t1"] is None or latest_data["t2"] is None:
        return  # ข้อมูลยังไม่พร้อม

    now = datetime.now()
    hour = now.hour

    filename = DAY_FILE if 6 <= hour < 18 else NIGHT_FILE
    temp_record = {
        "time": now.strftime("%H:%M"),
        "t1": latest_data["t1"],
        "t2": latest_data["t2"]
    }

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    data.append(temp_record)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)



def calculate_and_log_average():
    def load_temps(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    day_data = load_temps(DAY_FILE)
    night_data = load_temps(NIGHT_FILE)

    def average_temp(data):
        if not data:
            return None
        t1_avg = sum(d["t1"] for d in data) / len(data)
        t2_avg = sum(d["t2"] for d in data) / len(data)
        return (t1_avg + t2_avg) / 2

    day_avg = average_temp(day_data)
    night_avg = average_temp(night_data)

    date_str = datetime.now().strftime("%d/%m/%Y")
    with open(TEMP_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"📅 วันที่ {date_str}\n")
        f.write(f"🌤️ กลางวันเฉลี่ย: {day_avg:.2f}°C\n" if day_avg else "ไม่มีข้อมูลกลางวัน\n")
        f.write(f"🌙 กลางคืนเฉลี่ย: {night_avg:.2f}°C\n" if night_avg else "ไม่มีข้อมูลกลางคืน\n")
        f.write("-" * 40 + "\n")

    # ลบ json เตรียมใช้ใหม่วันถัดไป
    for file in [DAY_FILE, NIGHT_FILE]:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
