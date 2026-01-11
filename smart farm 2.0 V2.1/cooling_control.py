import asyncio
from log import setup_logger
from fan_sys import fan1_on, fan1_off, fan2_on, fan2_off, fan3_on, fan3_off, fan4_on, fan4_off
from watering import watering3, watering3_stop

logger = setup_logger()
fan_on = False
sprinkler_on = False

def cooling_control(ser, temp1, temp2, humid1, humid2, sensor_agree):
    global fan_on, sprinkler_on

    if None in (temp1, temp2):
        logger.warning("❌ ไม่มีข้อมูลอุณหภูมิ")
        return

    used_temp = max(temp1, temp2)
    use_humid = max(humid1, humid2)
    msg = f"[Cooling] ใช้อุณหภูมิ {'สูงสุด' if not sensor_agree else 'sensor OK'}: {used_temp:.2f} °C ความชื้น: {use_humid:.2f}%"
    logger.info(msg)

    if use_humid > 40 and fan_on and not sprinkler_on:
        logger.info("✅ เปิดการฉีดน้ำเพิ่มความชื้น")
        watering3(ser)
        sprinkler_on = True
    
    elif use_humid < 70 and not fan_on and sprinkler_on:
        logger.info("✅ หยุดการฉีดน้ำ")
        watering3_stop(ser)
        sprinkler_on = False
    
    if used_temp > 50 and not fan_on:
        logger.info("❗ เปิดพัดลม (Temp > 50°C)")
        fan1_on(),fan2_on(),fan3_on(),fan4_on()
        fan_on = True
    elif used_temp < 40 and fan_on:
        logger.info("✅ ปิดพัดลม (Temp < 40°C)")
        fan1_off(),fan2_off(),fan3_off(),fan4_off()
        fan_on = False