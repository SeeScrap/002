import asyncio
from log import setup_logger

logger = setup_logger()

async def watering(ser):
    logger.info("🚿 เริ่มรดน้ำ")
    ser.write(b"relay_on 2\n")
    await asyncio.sleep(10)  # ใช้ await แทน time.sleep
    logger.info("⛔ หยุดรดน้ำ")
    ser.write(b"relay_off 2\n")
