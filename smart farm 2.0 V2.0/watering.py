import asyncio
from log import setup_logger

logger = setup_logger()

async def watering1(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    ser.write(b"relay_on 1\n")
    
async def watering1_stop(ser):
    logger.info("⛔ หยุดรดน้ำ")
    ser.write(b"relay_off 1\n")
    
    
async def watering2(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    ser.write(b"relay_on 2\n")
    
async def watering2_stop(ser):
    logger.info("⛔ หยุดรดน้ำ")
    ser.write(b"relay_off 2\n")
