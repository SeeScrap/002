import asyncio
from log import setup_logger
from fan_sys import fan1_on, fan1_off, fan2_on, fan2_off, fan3_on, fan3_off, fan4_on, fan4_off
from watering import watering3, watering3_stop
from error_report import report_error
import state_manager

logger = setup_logger()
fan_on = False
sprinkler_on = False

def cooling_control(ser, temp1, temp2, humid1, humid2, sensor_agree):
    global fan_on, sprinkler_on

    try:
        if None in (temp1, temp2):
            logger.warning("❌ ไม่มีข้อมูลอุณหภูมิ")
            return

        # ป้องกัน None ใน humidity
        if humid1 is None and humid2 is None:
            logger.warning("❌ ไม่มีข้อมูลความชื้น")
            return

        used_temp = max(temp1, temp2)

        # คำนวณ humidity อย่างปลอดภัย
        if humid1 is not None and humid2 is not None:
            use_humid = max(humid1, humid2)
        elif humid1 is not None:
            use_humid = humid1
        else:
            use_humid = humid2

        logger.info(
            f"[Cooling] ใช้อุณหภูมิ {'สูงสุด' if not sensor_agree else 'sensor OK'}: {used_temp:.2f} °C ความชื้น: {use_humid:.2f}%"
        )

        # ระบบฉีดน้ำเพิ่มความชื้น
        if use_humid < 40 and fan_on and not sprinkler_on:
            logger.info("✅ เปิดการฉีดน้ำเพิ่มความชื้น")
            watering3(ser)
            sprinkler_on = True
            state_manager.set_device_state(sprinkler_on=True)

        elif use_humid > 70 and sprinkler_on:
            logger.info("✅ หยุดการฉีดน้ำ")
            watering3_stop(ser)
            sprinkler_on = False
            state_manager.set_device_state(sprinkler_on=False)

        # พัดลม
        if used_temp >= 27 and not fan_on:
            logger.info("❗ เปิดพัดลม (Temp ≥ 27°C)")
            for fan in (fan1_on, fan2_on, fan3_on, fan4_on):
                fan(ser)
            fan_on = True
            state_manager.set_device_state(fan_on=True)

        elif used_temp <= 26 and fan_on:
            logger.info("✅ ปิดพัดลม (Temp ≤ 26°C)")
            for fan in (fan1_off, fan2_off, fan3_off, fan4_off):
                fan(ser)
            fan_on = False
            state_manager.set_device_state(fan_on=False)

    except Exception as e:
        report_error("cooling_control", e, "ระบบควบคุมความเย็น")


def restore_device_states(ser):
    """กู้คืนสถานะอุปกรณ์จาก state ที่บันทึกไว้ (เรียกหลัง reboot)"""
    global fan_on, sprinkler_on
    try:
        saved = state_manager.get_device_state()
        if saved.get("fan_on"):
            logger.info("[Cooling] กู้คืนสถานะ: เปิดพัดลมทั้งหมด")
            for fan in (fan1_on, fan2_on, fan3_on, fan4_on):
                fan(ser)
            fan_on = True
        if saved.get("sprinkler_on"):
            logger.info("[Cooling] กู้คืนสถานะ: เปิดการฉีดน้ำ")
            watering3(ser)
            sprinkler_on = True
    except Exception as e:
        report_error("cooling_control", e, "กู้คืนสถานะอุปกรณ์")