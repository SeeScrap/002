from log import setup_logger

logger = setup_logger()

def check_sensor_agreement(t1, t2, h1, h2):
    if None in (t1, t2, h1, h2):
        logger.warning("⚠️ ข้อมูลเซ็นเซอร์ไม่ครบ")
        return False

    temp_diff = abs(t1 - t2)
    humid_diff = abs(h1 - h2)

    if temp_diff > 5:
        logger.warning(f"⚠️ อุณหภูมิคลาดเคลื่อนเกิน 5°C: {temp_diff:.2f}")
    if humid_diff > 5:
        logger.warning(f"⚠️ ความชื้นคลาดเคลื่อนเกิน 5%: {humid_diff:.2f}")

    return temp_diff <= 5 and humid_diff <= 5