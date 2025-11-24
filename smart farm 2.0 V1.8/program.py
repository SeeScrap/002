import serial
import schedule
import time
import serial.tools.list_ports
import asyncio

from read_sensor_all import read_sensor_all
from watering import watering
from cooling_control import cooling_control
import weather_report
from weather_report import latest_data
from log import setup_logger

logger = setup_logger()
ser = None


# ฟังก์ชันการทำงานของโปรแกรม
def job_read_all():
    t1, t2, h1, h2, agree = read_sensor_all(ser)
    latest_data.update({
        "t1": t1, "t2": t2, "h1": h1, "h2": h2, "agree": agree
    })
# ฟังก์ชันการทำงานของโปรแกรม
def job_cooling():
    cooling_control(ser, latest_data["t1"], latest_data["t2"], latest_data["agree"])





async def scheduler_loop():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)  # ใช้ await แทน time.sleep





async def program1():
    schedule.every(15).minutes.do(job_read_all)
    schedule.every(30).minutes.do(job_cooling)
    schedule.every(15).minutes.do(weather_report.append_temp_to_json)
    schedule.every().day.at("07:00").do(watering, ser)
    schedule.every().day.at("19:05").do(watering, ser)
    schedule.every().day.at("23:59").do(weather_report.calculate_and_log_average)
    logger.info("โปรแกรม 1 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler อย่างต่อเนื่อง
    
    
async def program2():
    schedule.every(15).minutes.do(job_read_all)
    schedule.every(30).minutes.do(job_cooling)
    schedule.every(15).minutes.do(weather_report.append_temp_to_json)
    schedule.every().day.at("07:00").do(watering, ser)
    schedule.every().day.at("19:05").do(watering, ser)
    schedule.every().day.at("23:59").do(weather_report.calculate_and_log_average)
    logger.info("โปรแกรม 2 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler อย่างต่อเนื่อง
    
    
async def program3():
    schedule.every(15).minutes.do(job_read_all)
    schedule.every(30).minutes.do(job_cooling)
    schedule.every(15).minutes.do(weather_report.append_temp_to_json)
    schedule.every().day.at("07:00").do(watering, ser)
    schedule.every().day.at("18:00").do(watering, ser)
    schedule.every().day.at("23:59").do(weather_report.calculate_and_log_average)
    logger.info("โปรแกรม 3 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler อย่างต่อเนื่อง
    
    
async def program4():
    schedule.every(15).minutes.do(job_read_all)
    schedule.every(30).minutes.do(job_cooling)
    schedule.every(15).minutes.do(weather_report.append_temp_to_json)
    schedule.every().day.at("07:00").do(watering, ser)
    schedule.every().day.at("18:00").do(watering, ser)
    schedule.every().day.at("23:59").do(weather_report.calculate_and_log_average)
    logger.info("โปรแกรม 4 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler อย่างต่อเนื่อง
    
    
    
    