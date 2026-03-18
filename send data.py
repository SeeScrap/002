import firebase_admin
from firebase_admin import credentials, firestore
import time
import random
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

APP_ID = "smart-farm-v1"
COLLECTION_PATH = f"artifacts/{APP_ID}/public/data/logs"

print("--- Smart Farm Pi 5 Sender Started ---")

def read_sensors():
    """ฟังก์ชันจำลองการอ่านค่าจากเซนเซอร์"""
    temp = round(random.uniform(25.0, 35.0), 1)
    humi = round(random.uniform(50.0, 80.0), 1)
    light = random.randint(300, 800)
    return temp, humi, light

try:
    while True:
        # ✅ เวลาเครื่อง (local time)
        now = datetime.now()

        # อ่านค่า
        temperature, humidity, light = read_sensors()
        
        # ✅ เตรียมข้อมูล (เพิ่มวันที่)
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "light": light,

            # เวลาฝั่ง server (แม่นสุด)
            "timestamp": firestore.SERVER_TIMESTAMP,

            # ✅ เพิ่มวันที่อ่านง่าย
            "date": now.strftime("%Y-%m-%d"),

            # ✅ เพิ่มเวลาอ่านง่าย
            "time": now.strftime("%H:%M:%S"),

            # ✅ datetime เต็ม (เผื่อใช้กราฟ)
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # ส่งข้อมูล
        db.collection("artifacts").document(APP_ID)\
          .collection("public").document("data")\
          .collection("logs").add(data)
        
        print(f"[{now.strftime('%H:%M:%S')}] Data Sent: {temperature}°C, {humidity}%, {light}lx")
        
        time.sleep(10)

except KeyboardInterrupt:
    print("\nStopped by user")