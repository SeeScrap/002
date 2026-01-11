import asyncio
from log import setup_logger

logger = setup_logger()

def watering1(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    ser.write(b"relay_on 1\n")
    
def watering1_stop(ser):
    logger.info("⛔ หยุดรดน้ำ")
    ser.write(b"relay_off 1\n")
    
    
def watering2(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    ser.write(b"relay_on 2\n")
    
def watering2_stop(ser):
    logger.info("⛔ หยุดรดน้ำ")
    ser.write(b"relay_off 2\n")

def watering3(ser):
    logger.info("🚿 เริ่มปล่อยน้ำ")
    ser.write(b"relay_on 3\n")

def watering3_stop(ser):
    logger.info("⛔ หยุดปล่อยน้ำ")
    ser.write(b"relay_off 3\n")