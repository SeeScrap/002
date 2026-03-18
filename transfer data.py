import firebase_admin
from firebase_admin import credentials, firestore
import time
from datetime import datetime
from weather_report import latest_data
from log import setup_logger

logger = setup_logger()

# ─── Firebase Init ────────────────────────────────────────────
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

APP_ID = "smart-farm-v1"

print("--- Smart Farm Transfer Data Started ---")
logger.info("🚀 Transfer Data เริ่มทำงาน")


def transfer_data():
    """อ่านค่าจาก latest_data แล้วส่งขึ้น Firebase Firestore"""

    t1 = latest_data.get("t1")
    t2 = latest_data.get("t2")
    h1 = latest_data.get("h1")
    h2 = latest_data.get("h2")

    # ถ้ายังไม่มีข้อมูลจาก sensor ให้ข้ามไปก่อน
    if t1 is None and t2 is None:
        logger.warning("⏳ ยังไม่มีข้อมูล sensor — ข้ามการส่ง")
        return False

    # ✅ คำนวณค่าเฉลี่ยอุณหภูมิ (ถ้ามี 2 ตัว ใช้เฉลี่ย / ถ้ามีตัวเดียวก็ใช้ตัวนั้น)
    if t1 is not None and t2 is not None:
        temperature = round((t1 + t2) / 2, 1)
    else:
        temperature = round(t1 if t1 is not None else t2, 1)

    # ✅ คำนวณค่าเฉลี่ยความชื้น
    if h1 is not None and h2 is not None:
        humidity = round((h1 + h2) / 2, 1)
    else:
        humidity = round(h1 if h1 is not None else (h2 if h2 is not None else 0), 1)

    # ⚠️ ถ้าระบบมีเซนเซอร์วัดแสง ให้เปลี่ยนตรงนี้เป็นค่าจริง
    light = latest_data.get("light", 0)

    now = datetime.now()

    # ✅ เตรียมข้อมูลตาม format ที่ web dashboard ต้องการ
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "light": light,

        # timestamp จาก server (แม่นที่สุด)
        "timestamp": firestore.SERVER_TIMESTAMP,

        # วันที่ / เวลา อ่านง่าย
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        # ✅ ส่งข้อมูลไปยัง Firestore ที่ path ตรงกับ web
        db.collection("artifacts").document(APP_ID) \
          .collection("public").document("data") \
          .collection("logs").add(data)

        logger.info(
            f"✅ [Firebase] ส่งสำเร็จ: {temperature}°C, {humidity}%, {light}lx "
            f"({now.strftime('%H:%M:%S')})"
        )
        return True

    except Exception as e:
        logger.error(f"❌ [Firebase] ส่งไม่สำเร็จ: {e}")
        return False
