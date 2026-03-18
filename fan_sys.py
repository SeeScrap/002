import asyncio
from log import setup_logger

logger = setup_logger()

def fan1_on(ser):
    logger.info("เปิดพัดลม 1")
    ser.write(b"relay_on 3\n")
    
def fan1_off(ser):
    logger.info("ปิดพัดลม 1")
    ser.write(b"relay_off 3\n")
    
def fan2_on(ser):
    logger.info("เปิดพัดลม 2")
    ser.write(b"relay_on 4\n")
    
def fan2_off(ser):
    logger.info("ปิดพัดลม 2")
    ser.write(b"relay_off 4\n")
    
def fan3_on(ser):
    logger.info("เปิดพัดลม 3")
    ser.write(b"relay_on 5\n")

def fan3_off(ser):
    logger.info("ปิดพัดลม 3")
    ser.write(b"relay_off 5\n")

def fan4_on(ser):
    logger.info("เปิดพัดลม 4")
    ser.write(b"relay_on 6\n")

def fan4_off(ser):
    logger.info("ปิดพัดลม 4")
    ser.write(b"relay_off 6\n")


