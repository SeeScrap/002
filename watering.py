import asyncio
from log import setup_logger
from error_report import report_serial_error

logger = setup_logger()

def _safe_write(ser, command, label):
    """เขียนคำสั่งไปยัง serial อย่างปลอดภัย"""
    if ser is None:
        logger.warning(f"[watering] ไม่สามารถ{label} — serial ไม่ได้เชื่อมต่อ")
        return False
    try:
        ser.write(command)
        return True
    except Exception as e:
        report_serial_error(e, label)
        return False

def watering1(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    _safe_write(ser, b"relay_on 1\n", "เริ่มรดน้ำ 1")
    
def watering1_stop(ser):
    logger.info("⛔ หยุดรดน้ำ")
    _safe_write(ser, b"relay_off 1\n", "หยุดรดน้ำ 1")
    
    
def watering2(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    _safe_write(ser, b"relay_on 2\n", "เริ่มรดน้ำ 2")
    
def watering2_stop(ser):
    logger.info("⛔ หยุดรดน้ำ")
    _safe_write(ser, b"relay_off 2\n", "หยุดรดน้ำ 2")

def watering3(ser):
    logger.info("🚿 เริ่มปล่อยน้ำ")
    _safe_write(ser, b"relay_on 3\n", "เริ่มปล่อยน้ำ 3")

def watering3_stop(ser):
    logger.info("⛔ หยุดปล่อยน้ำ")
    _safe_write(ser, b"relay_off 3\n", "หยุดปล่อยน้ำ 3")