import asyncio
from log import setup_logger

logger = setup_logger()

async def light1_on(ser):
    logger.info("💡 เปิดไฟ")
    ser.write(b"relay_on 3\n")
    
async def light1_off(ser):
    logger.info("💡 ปิดไฟ")
    ser.write(b"relay_off 3\n")
    
async def light2_on(ser):
    logger.info("💡 เปิดไฟ")
    ser.write(b"relay_on 4\n")
    
async def light2_off(ser):
    logger.info("💡 ปิดไฟ")
    ser.write(b"relay_off 4\n")
    
    