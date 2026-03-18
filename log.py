import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logger():
    logger = logging.getLogger("greenhouse_logger")
    if logger.handlers:
        return logger  # ป้องกันไม่ให้เพิ่ม handler ซ้ำ

    # สร้างโฟลเดอร์ log ถ้ายังไม่มี
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)

    # base log file
    log_file = os.path.join(log_dir, "log.txt")

    # ถ้าไฟล์ log เดิมมีอยู่แล้ว → เปลี่ยนชื่อเป็น log_stop
    if os.path.exists(log_file):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        stop_file = os.path.join(log_dir, f"log_stop_{timestamp}.txt")
        os.rename(log_file, stop_file)

    # สร้าง handler สำหรับ log ใหม่
    file_handler = TimedRotatingFileHandler(
        filename=log_file,  # base filename
        when="midnight",    # ทุกเที่ยงคืน
        interval=1,
        encoding='utf-8',
        utc=False
    )
    file_handler.suffix = "%d-%m-%Y.txt"  # รูปแบบชื่อไฟล์ log ตามวันที่

    formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
    file_handler.setFormatter(formatter)

    # แสดงผลบน console ด้วย
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
