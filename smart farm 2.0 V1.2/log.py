import logging
import time
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logger():
    logger = logging.getLogger("greenhouse_logger")
    if logger.handlers:
        return logger  # ป้องกันไม่ให้เพิ่ม handler ซ้ำ

    # สร้างโฟลเดอร์ log ถ้ายังไม่มี
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)

    # เขียน log ใหม่ทุกวัน เก็บแยกตามวันที่
    log_file = os.path.join(log_dir, "log")
    file_handler = TimedRotatingFileHandler(
        filename=log_file, # base filename
        when="midnight",   # ทุกเที่ยงคืน
        interval=1,
        encoding='utf-8',
        utc=False
    )
    file_handler.suffix = "%d-%m-%Y.txt"  # รูปแบบชื่อไฟล์ log
    
    file_handler.rolloverAt = time.time() - 1

    formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
    file_handler.setFormatter(formatter)

    # แสดงผลบน console ด้วย
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
