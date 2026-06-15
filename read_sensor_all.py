import time
from log import setup_logger
from check_sensor_agreement import check_sensor_agreement
from error_report import report_error, report_serial_error, report_serial_ok
import state_manager

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

    # ─── Guard: ser is None (bypass mode / disconnected) ───
    if ser is None:
        logger.warning("[read_sensor_all] ไม่สามารถอ่านค่า — serial ไม่ได้เชื่อมต่อ")
        return latest_temp1, latest_temp2, latest_humid1, latest_humid2, latest_light, sensor_agree

    try:
        latest_temp1 = latest_temp2 = latest_humid1 = latest_humid2 = None
        latest_light = None

        # ─── อ่านอุณหภูมิและความชื้น ───
        try:
            ser.write(b"get_temp_all\n")
        except Exception as e:
            report_serial_error(e, "get_temp_all write")
            return latest_temp1, latest_temp2, latest_humid1, latest_humid2, latest_light, sensor_agree

        time.sleep(1)  # รอให้ ESP32 ส่งข้อมูลกลับมา

        timeout = time.time() + 5 
        while time.time() < timeout and (latest_temp1 is None or latest_temp2 is None):
            try:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    logger.info(f"ESP32: {line}")

                    if "BME1 TEMP" in line:
                        try:
                            latest_temp1 = float(line.split("TEMP:")[1].split("C")[0].strip())
                            latest_humid1 = float(line.split("HUMID:")[1].split("%")[0].strip())
                        except (ValueError, IndexError) as e:
                            logger.warning(f"❌ ไม่สามารถ parse ค่า BME1: {e}")

                    elif "BME2 TEMP" in line:
                        try:
                            latest_temp2 = float(line.split("TEMP:")[1].split("C")[0].strip())
                            latest_humid2 = float(line.split("HUMID:")[1].split("%")[0].strip())
                        except (ValueError, IndexError) as e:
                            logger.warning(f"❌ ไม่สามารถ parse ค่า BME2: {e}")

                else:
                    time.sleep(0.1)  # กัน loop วิ่ง 100% CPU
            except Exception as e:
                report_serial_error(e, "อ่านอุณหภูมิ/ความชื้น")
                break

        if latest_temp1 is None:
            logger.warning("❌ ไม่สามารถอ่านค่า BME1")
        if latest_temp2 is None:
            logger.warning("❌ ไม่สามารถอ่านค่า BME2")

        sensor_agree = check_sensor_agreement(latest_temp1, latest_temp2, latest_humid1, latest_humid2)

        # ─── อ่านความชื้นในดิน ───
        try:
            ser.write(b"get_soil\n")
        except Exception as e:
            report_serial_error(e, "get_soil write")

        timeout = time.time() + 4
        while time.time() < timeout:
            try:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    logger.info(f"ESP32: {line}")
                    if "SOIL:" in line:
                        break
                else:
                    time.sleep(0.1)
            except Exception as e:
                report_serial_error(e, "อ่านความชื้นดิน")
                break

        else:
            logger.warning("❌ ESP32: ไม่ส่งข้อมูล Sensor ความชื้นในดินกลับมา")

        # ─── อ่านค่าแสง (LDR / BH1750) ───
        try:
            ser.write(b"get_light\n")
        except Exception as e:
            report_serial_error(e, "get_light write")

        time.sleep(0.2)
        timeout = time.time() + 4
        while time.time() < timeout:
            try:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='replace').strip()
                    logger.info(f"ESP32: {line}")
                    if "LIGHT:" in line:
                        try:
                            latest_light = int(line.split("LIGHT:")[1].strip().split()[0])
                            logger.info(f"💡 Light: {latest_light} lx")
                        except (ValueError, IndexError):
                            logger.warning("❌ ไม่สามารถ parse ค่าแสงได้")
                        break
                time.sleep(0.05)
            except Exception as e:
                report_serial_error(e, "อ่านค่าแสง")
                break

        if latest_light is None:
            logger.warning("❌ ไม่สามารถอ่านค่าเซ็นเซอร์แสง")

        # ─── Serial OK — reset error counter ───
        report_serial_ok()

        # ─── บันทึก sensor data ลง state ───
        state_manager.set_sensor_data(
            t1=latest_temp1, t2=latest_temp2,
            h1=latest_humid1, h2=latest_humid2,
            light=latest_light, agree=sensor_agree
        )

        # หมายเหตุ: cooling_control ถูกเรียกใน job_all() ที่ program.py แล้ว — ไม่เรียกซ้ำที่นี่

        return latest_temp1, latest_temp2, latest_humid1, latest_humid2, latest_light, sensor_agree

    except Exception as e:
        report_error("read_sensor_all", e, "อ่านค่าเซ็นเซอร์ทั้งหมด")
        return latest_temp1, latest_temp2, latest_humid1, latest_humid2, latest_light, sensor_agree
