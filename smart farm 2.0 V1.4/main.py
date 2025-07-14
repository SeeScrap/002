import serial
import schedule
import time
import serial.tools.list_ports

from read_sensor_all import read_sensor_all
from watering import watering
from cooling_control import cooling_control
import weather_report
from weather_report import latest_data
from log import setup_logger
from UI import UI

logger = setup_logger()
ser = None


# ฟังก์ชันเริ่มต้นโปรแกรม
def find_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "USB" in port.description or "ttyACM" in port.device:
            return port.device
    return None
# ฟังก์ชันการทำงานของโปรแกรม
def job_read_all():
    t1, t2, h1, h2, agree = read_sensor_all(ser)
    latest_data.update({
        "t1": t1, "t2": t2, "h1": h1, "h2": h2, "agree": agree
    })
# ฟังก์ชันการทำงานของโปรแกรม
def job_cooling():
    cooling_control(ser, latest_data["t1"], latest_data["t2"], latest_data["agree"])

schedule.every(15).minutes.do(job_read_all)
schedule.every(30).minutes.do(job_cooling)
schedule.every(15).minutes.do(weather_report.append_temp_to_json)
schedule.every().day.at("07:00").do(watering, ser)
schedule.every().day.at("18:00").do(watering, ser)
schedule.every().day.at("23:59").do(weather_report.calculate_and_log_average)


#เริ่มต้นโปรแกรม
UI()
while ser is None:
    esp_port = find_esp32_port()
    if esp_port:
        try:
            ser = serial.Serial(esp_port, 115200, timeout=1)
            logger.info(f"✅ Connected to ESP32 at {esp_port}")
        except Exception as e:
            logger.error(f"❌ ไม่สามารถเชื่อมต่อกับ {esp_port}: {e}")
            ser = None
    else:
        logger.warning("❌ ไม่พบ ESP32 — กำลังรอการเชื่อมต่อ...")
    time.sleep(5)  # รอ 5 วิ แล้วลองใหม่

while True:
        schedule.run_pending()
        time.sleep(1)