import time
from datetime import datetime
from weather_report import latest_data
from log import setup_logger
from error_report import report_error

logger = setup_logger()

# ─── Firebase Lazy Init ──────────────────────────────────────
_db = None
_firebase_initialized = False
_firebase_init_error_count = 0
_MAX_INIT_RETRIES = 3

APP_ID = "smart-farm-v1"


def _init_firebase():
    """เริ่มต้น Firebase แบบ lazy — ไม่ crash ถ้าล้มเหลว"""
    global _db, _firebase_initialized, _firebase_init_error_count

    if _firebase_initialized:
        return _db is not None

    if _firebase_init_error_count >= _MAX_INIT_RETRIES:
        return False  # ลองเกินจำนวนครั้งแล้ว

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # ตรวจสอบว่า app ถูก initialize แล้วหรือยัง
        try:
            app = firebase_admin.get_app()
        except ValueError:
            # ยังไม่ได้ initialize
            import os
            key_file = "serviceAccountKey.json"
            if not os.path.exists(key_file):
                logger.error(f"[Firebase] ไม่พบไฟล์ {key_file}")
                _firebase_init_error_count += 1
                return False

            cred = credentials.Certificate(key_file)
            firebase_admin.initialize_app(cred)

        _db = firestore.client()
        _firebase_initialized = True
        logger.info("🚀 Transfer Data — Firebase เชื่อมต่อสำเร็จ")
        return True

    except Exception as e:
        _firebase_init_error_count += 1
        report_error("transfer_data", e, f"Firebase init (ครั้งที่ {_firebase_init_error_count}/{_MAX_INIT_RETRIES})")
        return False


def transfer_data():
    """อ่านค่าจาก latest_data แล้วส่งขึ้น Firebase Firestore"""
    try:
        # ─── Firebase lazy init ───
        if not _init_firebase():
            logger.warning("[Firebase] ยังไม่สามารถเชื่อมต่อ Firebase ได้ — ข้ามการส่ง")
            return False

        from firebase_admin import firestore

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

        # ✅ ส่งข้อมูลไปยัง Firestore ที่ path ตรงกับ web
        _db.collection("artifacts").document(APP_ID) \
          .collection("public").document("data") \
          .collection("logs").add(data)

        logger.info(
            f"✅ [Firebase] ส่งสำเร็จ: {temperature}°C, {humidity}%, {light}lx "
            f"({now.strftime('%H:%M:%S')})"
        )
        return True

    except Exception as e:
        report_error("transfer_data", e, "ส่งข้อมูล Firebase")
        return False
