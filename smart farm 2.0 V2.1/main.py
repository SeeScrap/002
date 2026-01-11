import serial
import time
import serial.tools.list_ports
import asyncio

from log import setup_logger
from UI import UI
from program import program1, program2, program3, program4, ser
import os

logger = setup_logger()


# ฟังก์ชันค้นหาพอร์ตที่เชื่อมต่อกับ ESP32
def find_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "USB" in port.description or "ttyACM" in port.device:
            return port.device
    return None


# จัดการการเลือกโปรแกรมและบันทึกลงไฟล์เพื่อให้จำข้ามรีบู๊ต
SEL_FILE = "selected_program.txt"

def save_selection(n1, n2):
    try:
        with open(SEL_FILE, "w") as f:
            f.write(f"{n1},{n2}")
            logger.info(f"บันทึกการตั้งค่าโปรแกรม: {n1}, {n2}")
    except Exception as e:
        logger.error(f"ไม่สามารถบันทึกการตั้งค่า: {e}")

def load_selection():
    try:
        with open(SEL_FILE, "r") as f:
            v = f.read().strip()
            parts = v.split(",")
            if len(parts) == 2 and parts[0] in ("1","2","3","4") and parts[1] in ("1","2","3","4"):
                return parts[0], parts[1]
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"ไม่สามารถโหลดการตั้งค่า: {e}")
    return None

async def run_programs(p1, p2):
    print(f"รันโปรแกรม {p1} และ {p2} พร้อมกัน...")
    await asyncio.gather(
        globals()[f"program{p1}"](),
        globals()[f"program{p2}"]()
    )


# ถ้ามีการตั้งค่าเดิมให้เรียกใช้งานต่อทันที
async def main():

    # โหลดค่าเก่า
    sel = load_selection()
    if sel:
        p1, p2 = sel
        print(f"พบการตั้งค่าเดิม: {p1}, {p2} — กำลังโหลด...")
        time.sleep(1)
        await run_programs(p1, p2)
        logger.info(f"โหลดการตั้งค่าโปรแกรมเดิม: {p1}, {p2}")
        return

    # ไม่มีค่าเดิม → ให้เลือกใหม่
    while True:
        p1 = input("เลือกโปรแกรมย่อยตัวที่ 1 (1-4): ")
        p2 = input("เลือกโปรแกรมย่อยตัวที่ 2 (1-4): ")

        if p1 in ("1","2","3","4") and p2 in ("1","2","3","4"):
            save_selection(p1, p2)
            await run_programs(p1, p2)
            return
        else:
            print("เลือกได้เฉพาะ 1-4 เท่านั้น")




#เริ่มต้นโปรแกรม
UI()
# กำหนดวิธี bypass: ตั้งตัวแปรแวดล้อม BYPASS_ESP32=1 หรือสร้างไฟล์ชื่อ "bypass_esp32"
bypass = os.getenv("BYPASS_ESP32", "0") == "1" or os.path.exists("bypass_esp32")
if bypass:
    logger.warning("⚠️ ESP32 bypass enabled — ข้ามการเชื่อมต่อ serial")
    time.sleep(1)
else:
    while ser is None:
        esp_port = find_esp32_port()
        if esp_port:
            try:
                ser = serial.Serial(esp_port, 115200, timeout=1)
                logger.info(f"✅ Connected to ESP32 at {esp_port}")
                
                # Inject ser into program module so it can be used there
                import program
                program.ser = ser
                
                time.sleep(2)  # รอให้การเชื่อมต่อเสถียรก่อน
            except Exception as e:
                logger.error(f"❌ ไม่สามารถเชื่อมต่อกับ {esp_port}: {e}")
                ser = None
        else:
            logger.warning("❌ ไม่พบ ESP32 — กำลังรอการเชื่อมต่อ...")
        time.sleep(5)  # รอ 5 วิ แล้วลองใหม่

if __name__ == "__main__":
    asyncio.run(main())

