import asyncio
from log import setup_logger
from error_report import report_serial_error

logger = setup_logger()

def _safe_write(ser, command, label):
    """เขียนคำสั่งไปยัง serial อย่างปลอดภัย"""
    if ser is None:
        logger.warning(f"[fan_sys] ไม่สามารถ{label} — serial ไม่ได้เชื่อมต่อ")
        return False
    try:
        ser.write(command)
        return True
    except Exception as e:
        report_serial_error(e, label)
        return False

def fan1_on(ser):
    logger.info("เปิดพัดลม 1")
    _safe_write(ser, b"relay_on 3\n", "เปิดพัดลม 1")
    
def fan1_off(ser):
    logger.info("ปิดพัดลม 1")
    _safe_write(ser, b"relay_off 3\n", "ปิดพัดลม 1")
    
def fan2_on(ser):
    logger.info("เปิดพัดลม 2")
    _safe_write(ser, b"relay_on 4\n", "เปิดพัดลม 2")
    
def fan2_off(ser):
    logger.info("ปิดพัดลม 2")
    _safe_write(ser, b"relay_off 4\n", "ปิดพัดลม 2")
    
def fan3_on(ser):
    logger.info("เปิดพัดลม 3")
    _safe_write(ser, b"relay_on 5\n", "เปิดพัดลม 3")

def fan3_off(ser):
    logger.info("ปิดพัดลม 3")
    _safe_write(ser, b"relay_off 5\n", "ปิดพัดลม 3")

def fan4_on(ser):
    logger.info("เปิดพัดลม 4")
    _safe_write(ser, b"relay_on 6\n", "เปิดพัดลม 4")

def fan4_off(ser):
    logger.info("ปิดพัดลม 4")
    _safe_write(ser, b"relay_off 6\n", "ปิดพัดลม 4")


