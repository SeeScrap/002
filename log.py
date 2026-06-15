import logging
import os
from datetime import datetime

_current_file_handler = None
_current_date = None

def setup_logger():
    global _current_file_handler, _current_date

    logger = logging.getLogger("greenhouse_logger")
    if logger.handlers:
        return logger  # ป้องกันไม่ให้เพิ่ม handler ซ้ำ

    # สร้างโฟลเดอร์ log ถ้ายังไม่มี
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)

    # ตั้งชื่อไฟล์ตามวันที่
    today = datetime.now().strftime("%d-%m-%Y")
    _current_date = today
    log_file = os.path.join(log_dir, f"log_{today}.txt")

    # ถ้าไฟล์ log วันนี้มีอยู่แล้ว (restart ระหว่างวัน) → เปลี่ยนชื่อเป็น log_stop
    if os.path.exists(log_file):
        try:
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            stop_file = os.path.join(log_dir, f"log_stop_{timestamp}.txt")
            os.rename(log_file, stop_file)
        except OSError:
            # ไฟล์อาจถูกล็อกอยู่ — ลองใช้ copy แทน
            try:
                import shutil
                timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                stop_file = os.path.join(log_dir, f"log_stop_{timestamp}.txt")
                shutil.copy2(log_file, stop_file)
                try:
                    os.remove(log_file)
                except OSError:
                    pass
            except Exception:
                pass  # ล้มเหลวทั้งหมด — ปล่อย handler เขียนต่อไฟล์เดิม

    # สร้าง handler สำหรับ log ใหม่
    _current_file_handler = logging.FileHandler(
        filename=log_file,
        encoding='utf-8'
    )

    formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
    _current_file_handler.setFormatter(formatter)

    # แสดงผลบน console ด้วย
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(_current_file_handler)
    logger.addHandler(stream_handler)

    return logger


def check_log_rotation():
    """
    เรียกจาก scheduler ทุกนาที — ถ้าข้ามวันจะเปลี่ยนไฟล์ log ให้ตรงวันที่ใหม่
    เช่น log_15-06-2026.txt → log_16-06-2026.txt
    """
    global _current_file_handler, _current_date

    today = datetime.now().strftime("%d-%m-%Y")
    if today == _current_date:
        return  # ยังวันเดิม — ไม่ต้องทำอะไร

    logger = logging.getLogger("greenhouse_logger")
    log_dir = "log"
    new_file = os.path.join(log_dir, f"log_{today}.txt")

    try:
        # ลบ handler เก่า
        if _current_file_handler:
            logger.removeHandler(_current_file_handler)
            _current_file_handler.close()

        # สร้าง handler ใหม่สำหรับวันใหม่
        formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
        _current_file_handler = logging.FileHandler(new_file, encoding='utf-8')
        _current_file_handler.setFormatter(formatter)
        logger.addHandler(_current_file_handler)

        _current_date = today
        logger.info(f"📅 เริ่ม log วันใหม่: log_{today}.txt")

    except Exception as e:
        print(f"[log] ไม่สามารถหมุนไฟล์ log: {e}")
