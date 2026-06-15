import serial
import schedule
import time
import serial.tools.list_ports
import asyncio

from read_sensor_all import read_sensor_all
from watering import watering1, watering1_stop, watering2, watering2_stop
from fan_sys import fan1_on, fan1_off, fan2_on, fan2_off, fan3_on, fan3_off, fan4_on, fan4_off
from cooling_control import cooling_control
import weather_report
from weather_report import latest_data
from log import setup_logger, check_log_rotation
from transfer_data import transfer_data
from error_report import report_error
import state_manager

logger = setup_logger()
ser = None

# ─── ติดตาม job tag เพื่อป้องกันการลงทะเบียนซ้ำ ─────────────
_registered_tags = set()


def _register_job_once(tag, scheduler_call, *args):
    """ลงทะเบียน schedule job เฉพาะครั้งแรก — ป้องกันซ้ำซ้อน"""
    if tag in _registered_tags:
        logger.debug(f"[schedule] ข้าม job ที่ซ้ำ: {tag}")
        return
    _registered_tags.add(tag)
    scheduler_call(*args).tag(tag)


# ฟังก์ชันการทำงานของโปรแกรม
def job_read_all():
    try:
        t1, t2, h1, h2, light, agree = read_sensor_all(ser)
        latest_data.update({
            "t1": t1, "t2": t2, "h1": h1, "h2": h2, "light": light, "agree": agree
        })
    except Exception as e:
        report_error("program", e, "job_read_all")

# ฟังก์ชันการทำงานของโปรแกรม
def job_all():
    try:
        job_read_all()
        cooling_control(ser, latest_data["t1"], latest_data["t2"],latest_data["h1"],latest_data["h2"], latest_data["agree"])
    except Exception as e:
        report_error("program", e, "job_all")


async def scheduler_loop():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            report_error("program", e, "scheduler_loop — run_pending")
        await asyncio.sleep(1)  # ใช้ await แทน time.sleep


def _register_common_jobs():
    """ลงทะเบียน job ที่ทุกโปรแกรมใช้ร่วมกัน"""
    _register_job_once("job_all_every_min",
        lambda: schedule.every(1).minutes.do(job_all))
    _register_job_once("transfer_data_every_hour",
        lambda: schedule.every(1).hours.do(transfer_data))
    _register_job_once("append_temp_60min",
        lambda: schedule.every(60).minutes.do(weather_report.append_temp_to_json))
    _register_job_once("calc_avg_daily",
        lambda: schedule.every().day.at("23:59").do(weather_report.calculate_and_log_average))
    _register_job_once("save_state_periodic",
        lambda: schedule.every(1).minutes.do(state_manager.save_if_dirty))
    _register_job_once("log_rotation_check",
        lambda: schedule.every(1).minutes.do(check_log_rotation))


async def program1():
    _register_common_jobs()
    _register_job_once("p1_water1_am",
        lambda: schedule.every().day.at("06:00").do(watering1, ser))
    _register_job_once("p1_water1_pm",
        lambda: schedule.every().day.at("18:00").do(watering1, ser))
    _register_job_once("p1_water1_stop_am",
        lambda: schedule.every().day.at("06:01").do(watering1_stop, ser))
    _register_job_once("p1_water1_stop_pm",
        lambda: schedule.every().day.at("18:01").do(watering1_stop, ser))
    logger.info("โปรแกรม 1 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler ไปเรื่อยๆ
    
    
async def program2():
    _register_common_jobs()
    _register_job_once("p2_water1_am",
        lambda: schedule.every().day.at("06:00").do(watering1, ser))
    _register_job_once("p2_water1_pm",
        lambda: schedule.every().day.at("18:00").do(watering1, ser))
    # ✅ แก้ไข: เดิมหยุดน้ำเวลาเดียวกับเปิดน้ำ (06:00/18:00) → แก้เป็น 06:01/18:01
    _register_job_once("p2_water1_stop_am",
        lambda: schedule.every().day.at("06:01").do(watering1_stop, ser))
    _register_job_once("p2_water1_stop_pm",
        lambda: schedule.every().day.at("18:01").do(watering1_stop, ser))
    logger.info("โปรแกรม 2 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler ไปเรื่อยๆ
    
    
async def program3():
    _register_common_jobs()
    _register_job_once("p3_water2_am",
        lambda: schedule.every().day.at("07:00").do(watering2, ser))
    _register_job_once("p3_water2_pm",
        lambda: schedule.every().day.at("19:00").do(watering2, ser))
    # ✅ แก้ไข: เดิมหยุดน้ำก่อนเปิด (06:00→07:00, 18:00→19:00) → แก้เป็น 07:01/19:01
    _register_job_once("p3_water2_stop_am",
        lambda: schedule.every().day.at("07:01").do(watering2_stop, ser))
    _register_job_once("p3_water2_stop_pm",
        lambda: schedule.every().day.at("19:01").do(watering2_stop, ser))
    logger.info("โปรแกรม 3 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler ไปเรื่อยๆ
    
    
async def program4():
    _register_common_jobs()
    _register_job_once("p4_water2_am",
        lambda: schedule.every().day.at("07:00").do(watering2, ser))
    _register_job_once("p4_water2_pm",
        lambda: schedule.every().day.at("17:00").do(watering2, ser))
    # ✅ แก้ไข: เดิมหยุดน้ำก่อนเปิด → แก้เป็น 07:01/17:01
    _register_job_once("p4_water2_stop_am",
        lambda: schedule.every().day.at("07:01").do(watering2_stop, ser))
    _register_job_once("p4_water2_stop_pm",
        lambda: schedule.every().day.at("17:01").do(watering2_stop, ser))
    logger.info("โปรแกรม 4 เริ่มทำงาน")
    await scheduler_loop()  # รัน loop ของ scheduler ไปเรื่อยๆ
    
    
    