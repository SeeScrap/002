import serial
import time
import serial.tools.list_ports
import asyncio
import os

from log import setup_logger
from UI import UI
from error_report import report_error
import state_manager

logger = setup_logger()


# ฟังก์ชันค้นหาพอร์ตที่เชื่อมต่อกับ ESP32
def find_esp32_port():
    try:
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "USB" in port.description or "ttyACM" in port.device or "CH340" in port.description:
                return port.device
        return None
    except Exception as e:
        report_error("main", e, "find_esp32_port")
        return None


# จัดการการเลือกโปรแกรมและบันทึกลงไฟล์เพื่อให้จำข้ามรีบู๊ต
SEL_FILE = "selected_program.txt"

def save_selection(n1, n2):
    try:
        with open(SEL_FILE, "w") as f:
            f.write(f"{n1},{n2}")
            logger.info(f"บันทึกการตั้งค่าโปรแกรม: {n1}, {n2}")
        # บันทึกลง state manager ด้วย
        state_manager.set_program_selection(n1, n2)
    except Exception as e:
        logger.error(f"ไม่สามารถบันทึกการตั้งค่า: {e}")

def load_selection():
    try:
        # ลองจาก state manager ก่อน
        sel = state_manager.get_program_selection()
        if sel:
            return sel

        # Fallback ไปที่ไฟล์เดิม
        with open(SEL_FILE, "r") as f:
            v = f.read().strip()
            parts = v.split(",")
            if len(parts) == 2 and parts[0] in ("1","2","3","4") and parts[1] in ("1","2","3","4"):
                # Sync กลับไปที่ state manager
                state_manager.set_program_selection(parts[0], parts[1])
                return parts[0], parts[1]
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"ไม่สามารถโหลดการตั้งค่า: {e}")
    return None


async def run_program_safe(program_func, name):
    """รัน program ใน exception barrier — restart ถ้า crash"""
    while True:
        try:
            await program_func()
        except asyncio.CancelledError:
            logger.info(f"โปรแกรม {name} ถูกยกเลิก")
            break
        except Exception as e:
            report_error("main", e, f"โปรแกรม {name} crash — restart ใน 10 วินาที")
            await asyncio.sleep(10)
            logger.info(f"🔄 กำลัง restart โปรแกรม {name}...")


async def run_programs(p1, p2):
    """รันสองโปรแกรมพร้อมกัน — ถ้าตัวหนึ่ง crash ไม่กระทบอีกตัว"""
    # นำเข้า program functions จาก program module
    import program
    program_map = {
        "1": program.program1,
        "2": program.program2,
        "3": program.program3,
        "4": program.program4,
    }

    func1 = program_map.get(p1)
    func2 = program_map.get(p2)

    if func1 is None or func2 is None:
        logger.error(f"โปรแกรมที่เลือกไม่ถูกต้อง: {p1}, {p2}")
        return

    print(f"รันโปรแกรม {p1} และ {p2} พร้อมกัน...")
    await asyncio.gather(
        run_program_safe(func1, f"program{p1}"),
        run_program_safe(func2, f"program{p2}"),
        return_exceptions=True
    )


async def serial_watchdog(check_interval=30):
    """
    Background task ที่ตรวจสอบสถานะ serial connection
    ถ้า serial หลุดจะลอง reconnect อัตโนมัติ
    """
    import program
    from error_report import should_reconnect_serial
    from cooling_control import restore_device_states

    while True:
        await asyncio.sleep(check_interval)
        try:
            if program.ser is None or should_reconnect_serial():
                logger.warning("🔄 [Watchdog] ตรวจพบ serial หลุด — กำลังลอง reconnect...")
                esp_port = find_esp32_port()
                if esp_port:
                    try:
                        # ปิด serial เก่าถ้ายังมี
                        if program.ser is not None:
                            try:
                                program.ser.close()
                            except Exception:
                                pass

                        new_ser = serial.Serial(esp_port, 115200, timeout=1)
                        program.ser = new_ser
                        state_manager.set_serial_info(port=esp_port, connected=True)
                        logger.info(f"✅ [Watchdog] Reconnect สำเร็จ: {esp_port}")

                        # กู้คืนสถานะอุปกรณ์
                        await asyncio.sleep(2)  # รอให้การเชื่อมต่อเสถียร
                        restore_device_states(program.ser)

                    except Exception as e:
                        report_error("main", e, f"Watchdog reconnect {esp_port}")
                else:
                    logger.debug("[Watchdog] ไม่พบ ESP32")

        except Exception as e:
            report_error("main", e, "serial_watchdog")


# ถ้ามีการตั้งค่าเดิมให้เรียกใช้งานต่อทันที
async def main():
    # เริ่ม serial watchdog เป็น background task
    watchdog_task = asyncio.create_task(serial_watchdog())

    # โหลดค่าเก่า
    sel = load_selection()
    if sel:
        p1, p2 = sel
        print(f"พบการตั้งค่าเดิม: {p1}, {p2} — กำลังโหลด...")
        await asyncio.sleep(1)
        await run_programs(p1, p2)
        logger.info(f"โหลดการตั้งค่าโปรแกรมเดิม: {p1}, {p2}")
        return

    # ไม่มีค่าเดิม → ให้เลือกใหม่
    while True:
        try:
            p1 = input("เลือกโปรแกรมย่อยตัวที่ 1 (1-4): ")
            p2 = input("เลือกโปรแกรมย่อยตัวที่ 2 (1-4): ")

            if p1 in ("1","2","3","4") and p2 in ("1","2","3","4"):
                save_selection(p1, p2)
                await run_programs(p1, p2)
                return
            else:
                print("เลือกได้เฉพาะ 1-4 เท่านั้น")
        except (EOFError, KeyboardInterrupt):
            logger.info("ผู้ใช้ยกเลิกการเลือก")
            break
        except Exception as e:
            report_error("main", e, "input loop")


if __name__ == "__main__":
    # ─── เริ่มต้นระบบ ───
    UI()

    # ─── โหลด state ───
    state_manager.load_state()

    # ─── กำหนดวิธี bypass ───
    bypass = os.getenv("BYPASS_ESP32", "0") == "1" or os.path.exists("bypass_esp32")

    import program

    if bypass:
        logger.warning("⚠️ ESP32 bypass enabled — ข้ามการเชื่อมต่อ serial")
        program.ser = None
        time.sleep(1)
    else:
        # ─── เชื่อมต่อ serial ───────────────────────────────
        connected = False
        for attempt in range(1, 61):  # ลองสูงสุด 60 ครั้ง (5 นาที)
            esp_port = find_esp32_port()
            if esp_port:
                try:
                    ser_conn = serial.Serial(esp_port, 115200, timeout=1)
                    program.ser = ser_conn
                    state_manager.set_serial_info(port=esp_port, connected=True)
                    logger.info(f"✅ Connected to ESP32 at {esp_port}")
                    time.sleep(2)  # รอให้การเชื่อมต่อเสถียรก่อน

                    # กู้คืนสถานะอุปกรณ์จาก state ที่บันทึกไว้
                    from cooling_control import restore_device_states
                    restore_device_states(program.ser)

                    connected = True
                    break
                except Exception as e:
                    logger.error(f"❌ ไม่สามารถเชื่อมต่อกับ {esp_port}: {e}")
                    program.ser = None
            else:
                logger.warning("❌ ไม่พบ ESP32 — กำลังรอการเชื่อมต่อ...")
            time.sleep(5)  # รอ 5 วิ แล้วลองใหม่

        if not connected:
            logger.warning("⚠️ ไม่สามารถเชื่อมต่อ ESP32 ได้ — เริ่มระบบแบบไม่มี serial (watchdog จะลอง reconnect)")

    # ─── รันโปรแกรมหลัก พร้อม top-level exception barrier ───
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 โปรแกรมถูกหยุดโดยผู้ใช้")
    except Exception as e:
        report_error("main", e, "top-level crash")
        logger.critical(f"💀 ข้อผิดพลาดร้ายแรง: {e}")
    finally:
        # บันทึก state ก่อนปิด
        state_manager.set_serial_info(connected=False)
        state_manager.save_state()
        logger.info("🔚 Smart Farm ปิดระบบ — state บันทึกแล้ว")
