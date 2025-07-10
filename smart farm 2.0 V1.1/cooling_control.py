from log import setup_logger

logger = setup_logger()
fan_on = False

def cooling_control(ser, temp1, temp2, sensor_agree):
    global fan_on

    if None in (temp1, temp2):
        logger.warning("❌ ไม่มีข้อมูลอุณหภูมิ")
        return

    used_temp = max(temp1, temp2)
    msg = f"[Cooling] ใช้อุณหภูมิ {'สูงสุด' if not sensor_agree else 'sensor OK'}: {used_temp:.2f} °C"
    logger.info(msg)

    if used_temp > 50 and not fan_on:
        logger.info("❗ เปิดพัดลม (Temp > 50°C)")
        ser.write(b"relay_on 1\n")
        fan_on = True
    elif used_temp < 40 and fan_on:
        logger.info("✅ ปิดพัดลม (Temp < 40°C)")
        ser.write(b"relay_off 1\n")
        fan_on = False