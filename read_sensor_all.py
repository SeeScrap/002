import time
from log import setup_logger
from check_sensor_agreement import check_sensor_agreement
from cooling_control import cooling_control

logger = setup_logger()

# ตัวแปรเก็บค่าล่าสุด
latest_temp1 = None
latest_temp2 = None
latest_humid1 = None
latest_humid2 = None
latest_light = None
sensor_agree = True

def read_sensor_all(ser):
    global latest_temp1, latest_temp2, latest_humid1, latest_humid2, latest_light, sensor_agree

    latest_temp1 = latest_temp2 = latest_humid1 = latest_humid2 = None
    latest_light = None

    ser.write(b"get_temp_all\n")
    time.sleep(0.2)

    timeout = time.time() + 5
    while time.time() < timeout and (latest_temp1 is None or latest_temp2 is None) and logger.warning("❌ ESP32: ไม่ส่งข้อมูล Sensor อุณภูมิกลับมา"):
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            logger.info(f"ESP32: {line}")
            if "BME1 TEMP" in line:
                try:
                    latest_temp1 = float(line.split("TEMP:")[1].split("C")[0].strip())
                    latest_humid1 = float(line.split("HUMID:")[1].split("%")[0].strip())
                except:
                    pass
            elif "BME2 TEMP" in line:
                try:
                    latest_temp2 = float(line.split("TEMP:")[1].split("C")[0].strip())
                    latest_humid2 = float(line.split("HUMID:")[1].split("%")[0].strip())
                except:
                    pass

    if latest_temp1 is None:
        logger.warning("❌ ไม่สามารถอ่านค่า BME1")
    if latest_temp2 is None:
        logger.warning("❌ ไม่สามารถอ่านค่า BME2")

    sensor_agree = check_sensor_agreement(latest_temp1, latest_temp2, latest_humid1, latest_humid2)

    # อ่านความชื้นในดิน
    ser.write(b"get_soil\n")
    timeout = time.time() + 4
    while time.time() < timeout and logger.warning("❌ ESP32: ไม่ส่งข้อมูล Sensor ความชื้นในดินกลับมา"):
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            logger.info(f"ESP32: {line}")
            if "SOIL:" in line:
                break

    # อ่านค่าแสง (LDR / BH1750)
    ser.write(b"get_light\n")
    time.sleep(0.2)
    timeout = time.time() + 4
    while time.time() < timeout:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            logger.info(f"ESP32: {line}")
            if "LIGHT:" in line:
                try:
                    latest_light = int(line.split("LIGHT:")[1].strip().split()[0])
                    logger.info(f"💡 Light: {latest_light} lx")
                except:
                    logger.warning("❌ ไม่สามารถ parse ค่าแสงได้")
                break
        time.sleep(0.05)

    if latest_light is None:
        logger.warning("❌ ไม่สามารถอ่านค่าเซ็นเซอร์แสง")

    cooling_control(ser, latest_temp1, latest_temp2, latest_humid1, latest_humid2, sensor_agree)

    return latest_temp1, latest_temp2, latest_humid1, latest_humid2, latest_light, sensor_agree
