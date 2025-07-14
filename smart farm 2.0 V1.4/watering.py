import time
from log import setup_logger

logger = setup_logger()

def watering(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    ser.write(b"relay_on 2\n")
    time.sleep(10)
    logger.info("⛔ หยุดรดน้ำ")
    ser.write(b"relay_off 2\n")