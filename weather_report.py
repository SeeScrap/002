import os
import json
from datetime import datetime
from log import setup_logger

logger = setup_logger()

LOG_DIR = "log"
DAY_FILE = os.path.join(LOG_DIR, "day.json")
NIGHT_FILE = os.path.join(LOG_DIR, "night.json")
TEMP_LOG_FILE = os.path.join(LOG_DIR, "temp_log_in_day.txt")

os.makedirs(LOG_DIR, exist_ok=True)

latest_data = {
    "t1": None,
    "t2": None,
    "h1": None,
    "h2": None,
    "light": None,
    "agree": True
}


def _safe_load_json(filename):
    """โหลด JSON อย่างปลอดภัย — คืน list เปล่าถ้าไฟล์ไม่มีหรือเสียหาย"""
    try:
        if not os.path.exists(filename):
            return []
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.warning(f"[weather_report] {filename} ไม่ใช่ list — reset")
            return []
    except json.JSONDecodeError as e:
        logger.warning(f"[weather_report] {filename} เสียหาย (JSON): {e} — reset")
        # เปลี่ยนชื่อไฟล์เสียหายเก็บไว้
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupt_name = f"{filename}.corrupt_{timestamp}"
            os.rename(filename, corrupt_name)
        except Exception:
            pass
        return []
    except Exception as e:
        logger.error(f"[weather_report] ไม่สามารถอ่าน {filename}: {e}")
        return []


def _safe_write_json(filename, data):
    """เขียน JSON อย่างปลอดภัย"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[weather_report] ไม่สามารถเขียน {filename}: {e}")


def append_temp_to_json():
    try:
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

        data = _safe_load_json(filename)
        data.append(temp_record)
        _safe_write_json(filename, data)

    except Exception as e:
        logger.error(f"[weather_report] append_temp_to_json ล้มเหลว: {e}")



def calculate_and_log_average():
    try:
        day_data = _safe_load_json(DAY_FILE)
        night_data = _safe_load_json(NIGHT_FILE)

        def average_temp(data):
            if not data:
                return None
            try:
                # กรองข้อมูลที่ไม่ถูกต้องออก
                valid = [d for d in data if isinstance(d.get("t1"), (int, float)) and isinstance(d.get("t2"), (int, float))]
                if not valid:
                    return None
                t1_avg = sum(d["t1"] for d in valid) / len(valid)
                t2_avg = sum(d["t2"] for d in valid) / len(valid)
                return (t1_avg + t2_avg) / 2
            except Exception as e:
                logger.error(f"[weather_report] คำนวณค่าเฉลี่ยล้มเหลว: {e}")
                return None

        day_avg = average_temp(day_data)
        night_avg = average_temp(night_data)

        date_str = datetime.now().strftime("%d/%m/%Y")
        try:
            with open(TEMP_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"📅 วันที่ {date_str}\n")
                f.write(f"🌤️ กลางวันเฉลี่ย: {day_avg:.2f}°C\n" if day_avg else "ไม่มีข้อมูลกลางวัน\n")
                f.write(f"🌙 กลางคืนเฉลี่ย: {night_avg:.2f}°C\n" if night_avg else "ไม่มีข้อมูลกลางคืน\n")
                f.write("-" * 40 + "\n")
        except Exception as e:
            logger.error(f"[weather_report] ไม่สามารถเขียน {TEMP_LOG_FILE}: {e}")

        # ลบ json เตรียมใช้ใหม่วันถัดไป
        for file in [DAY_FILE, NIGHT_FILE]:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.error(f"[weather_report] ไม่สามารถลบ {file}: {e}")

    except Exception as e:
        logger.error(f"[weather_report] calculate_and_log_average ล้มเหลว: {e}")
