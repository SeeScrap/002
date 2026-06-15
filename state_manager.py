"""
state_manager.py — ระบบจัดการสถานะแบบถาวร (Persistent State)
Saves and restores runtime state across reboots with validation and corruption recovery.
"""

import os
import json
import shutil
import time
from datetime import datetime
from log import setup_logger

logger = setup_logger()

# ─── Config ───────────────────────────────────────────────────
STATE_DIR = "state"
STATE_FILE = os.path.join(STATE_DIR, "runtime_state.json")
STATE_BACKUP = os.path.join(STATE_DIR, "runtime_state.backup.json")
CORRUPT_DIR = os.path.join(STATE_DIR, "corrupt")

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(CORRUPT_DIR, exist_ok=True)

# ─── Default State ────────────────────────────────────────────
DEFAULT_STATE = {
    "version": 2,  # schema version สำหรับ migration ในอนาคต
    "last_saved": None,
    "programs": {
        "p1": None,
        "p2": None
    },
    "devices": {
        "fan_on": False,
        "sprinkler_on": False
    },
    "sensors": {
        "t1": None,
        "t2": None,
        "h1": None,
        "h2": None,
        "light": None,
        "agree": True
    },
    "serial": {
        "last_port": None,
        "connected": False
    },
    "counters": {
        "boot_count": 0,
        "total_errors": 0,
        "last_boot": None
    }
}

# ─── In-memory state ─────────────────────────────────────────
_state = None
_dirty = False  # มีการเปลี่ยนแปลงที่ยังไม่ได้บันทึก


def _deep_copy(obj):
    """Deep copy ที่ปลอดภัย"""
    try:
        return json.loads(json.dumps(obj))
    except Exception:
        return {}


def _validate_state(data):
    """
    ตรวจสอบความถูกต้องของ state data
    คืนค่า (validated_data, is_valid)
    """
    if not isinstance(data, dict):
        return _deep_copy(DEFAULT_STATE), False

    valid = True
    result = _deep_copy(DEFAULT_STATE)

    # ─── version check ───
    version = data.get("version")
    if version != DEFAULT_STATE["version"]:
        logger.warning(f"[State] version mismatch: {version} != {DEFAULT_STATE['version']}")
        # ยังคง migrate ได้ — ไม่ถือว่า invalid

    # ─── programs ───
    programs = data.get("programs", {})
    if isinstance(programs, dict):
        for key in ("p1", "p2"):
            val = programs.get(key)
            if val is not None and str(val) in ("1", "2", "3", "4"):
                result["programs"][key] = str(val)
            elif val is not None:
                logger.warning(f"[State] ค่า programs.{key} ไม่ถูกต้อง: {val}")
                valid = False

    # ─── devices ───
    devices = data.get("devices", {})
    if isinstance(devices, dict):
        for key in ("fan_on", "sprinkler_on"):
            val = devices.get(key)
            if isinstance(val, bool):
                result["devices"][key] = val
            elif val is not None:
                # พยายามแปลง
                result["devices"][key] = bool(val)
                valid = False

    # ─── sensors ───
    sensors = data.get("sensors", {})
    if isinstance(sensors, dict):
        for key in ("t1", "t2", "h1", "h2", "light"):
            val = sensors.get(key)
            if val is None:
                result["sensors"][key] = None
            elif isinstance(val, (int, float)):
                result["sensors"][key] = val
            else:
                try:
                    result["sensors"][key] = float(val)
                except (ValueError, TypeError):
                    result["sensors"][key] = None
                    valid = False
        agree = sensors.get("agree")
        if isinstance(agree, bool):
            result["sensors"]["agree"] = agree

    # ─── serial ───
    serial_info = data.get("serial", {})
    if isinstance(serial_info, dict):
        result["serial"]["last_port"] = serial_info.get("last_port")
        result["serial"]["connected"] = bool(serial_info.get("connected", False))

    # ─── counters ───
    counters = data.get("counters", {})
    if isinstance(counters, dict):
        for key in ("boot_count", "total_errors"):
            val = counters.get(key)
            if isinstance(val, int) and val >= 0:
                result["counters"][key] = val
            elif val is not None:
                try:
                    result["counters"][key] = max(0, int(val))
                except (ValueError, TypeError):
                    pass
        result["counters"]["last_boot"] = counters.get("last_boot")

    # ─── timestamps ───
    result["last_saved"] = data.get("last_saved")
    result["version"] = DEFAULT_STATE["version"]

    return result, valid


def load_state():
    """
    โหลด state จากไฟล์ — ถ้าไฟล์เสียหายจะกู้คืนจาก backup
    คืนค่า state dict เสมอ (ไม่มีวัน return None)
    """
    global _state, _dirty

    # ลองโหลดจากไฟล์หลัก
    data = _try_load_file(STATE_FILE)
    if data is not None:
        validated, is_valid = _validate_state(data)
        if not is_valid:
            logger.warning("[State] ⚠️ state file มีข้อมูลบางส่วนไม่ถูกต้อง — ใช้ค่าที่แก้ไขแล้ว")
        _state = validated
        _state["counters"]["boot_count"] += 1
        _state["counters"]["last_boot"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _dirty = True
        save_state()
        logger.info(f"[State] ✅ โหลด state สำเร็จ (boot #{_state['counters']['boot_count']})")
        return _state

    # ไฟล์หลักเสียหาย — ลอง backup
    logger.warning("[State] ⚠️ ไฟล์ state หลักเสียหาย — กำลังลอง backup...")
    data = _try_load_file(STATE_BACKUP)
    if data is not None:
        validated, is_valid = _validate_state(data)
        _state = validated
        _state["counters"]["boot_count"] += 1
        _state["counters"]["last_boot"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _dirty = True
        save_state()
        logger.info("[State] ✅ กู้คืน state จาก backup สำเร็จ")
        return _state

    # ทั้งสองเสียหาย — ใช้ค่า default
    logger.warning("[State] ⚠️ ไม่สามารถโหลด state ได้ — ใช้ค่าเริ่มต้น")
    _state = _deep_copy(DEFAULT_STATE)
    _state["counters"]["boot_count"] = 1
    _state["counters"]["last_boot"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _dirty = True
    save_state()
    return _state


def _try_load_file(filepath):
    """ลองโหลด JSON จากไฟล์ — คืน None ถ้าล้มเหลว"""
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"[State] ไฟล์ {filepath} เสียหาย (JSON): {e}")
        _quarantine_file(filepath)
        return None
    except Exception as e:
        logger.error(f"[State] ไม่สามารถอ่าน {filepath}: {e}")
        return None


def _quarantine_file(filepath):
    """ย้ายไฟล์เสียหายไปเก็บไว้เพื่อตรวจสอบ"""
    try:
        if os.path.exists(filepath):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = os.path.basename(filepath)
            corrupt_path = os.path.join(CORRUPT_DIR, f"{timestamp}_{basename}")
            shutil.move(filepath, corrupt_path)
            logger.info(f"[State] ย้ายไฟล์เสียหายไป: {corrupt_path}")
    except Exception as e:
        logger.error(f"[State] ไม่สามารถย้ายไฟล์เสียหาย: {e}")


def save_state():
    """
    บันทึก state ลงไฟล์แบบ atomic (เขียน temp แล้ว rename)
    ปลอดภัยจากไฟดับระหว่างเขียน
    """
    global _dirty
    if _state is None:
        return

    try:
        _state["last_saved"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Backup ไฟล์เดิมก่อน
        if os.path.exists(STATE_FILE):
            try:
                shutil.copy2(STATE_FILE, STATE_BACKUP)
            except Exception:
                pass  # backup ล้มเหลวไม่เป็นไร

        # Atomic write: เขียน temp file ก่อนแล้ว rename
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(_state, f, indent=2, ensure_ascii=False)

        # Replace — บน Windows ต้องลบก่อน
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        os.rename(temp_file, STATE_FILE)

        _dirty = False

    except Exception as e:
        logger.error(f"[State] ❌ ไม่สามารถบันทึก state: {e}")


# ─── Convenience getters/setters ──────────────────────────────

def get_state():
    """คืนค่า state ปัจจุบัน (โหลดถ้ายังไม่ได้โหลด)"""
    global _state
    if _state is None:
        load_state()
    return _state


def set_device_state(fan_on=None, sprinkler_on=None):
    """อัพเดทสถานะอุปกรณ์และบันทึกทันที"""
    state = get_state()
    changed = False
    if fan_on is not None and state["devices"]["fan_on"] != fan_on:
        state["devices"]["fan_on"] = fan_on
        changed = True
    if sprinkler_on is not None and state["devices"]["sprinkler_on"] != sprinkler_on:
        state["devices"]["sprinkler_on"] = sprinkler_on
        changed = True
    if changed:
        save_state()


def set_sensor_data(t1=None, t2=None, h1=None, h2=None, light=None, agree=None):
    """อัพเดทข้อมูลเซ็นเซอร์"""
    state = get_state()
    sensors = state["sensors"]
    if t1 is not None:
        sensors["t1"] = t1
    if t2 is not None:
        sensors["t2"] = t2
    if h1 is not None:
        sensors["h1"] = h1
    if h2 is not None:
        sensors["h2"] = h2
    if light is not None:
        sensors["light"] = light
    if agree is not None:
        sensors["agree"] = agree
    # sensor data เปลี่ยนบ่อย — ยังไม่ save ทันที (รอ periodic save)
    global _dirty
    _dirty = True


def set_program_selection(p1, p2):
    """บันทึกโปรแกรมที่เลือก"""
    state = get_state()
    state["programs"]["p1"] = str(p1)
    state["programs"]["p2"] = str(p2)
    save_state()


def get_program_selection():
    """คืนค่าโปรแกรมที่เลือก — (p1, p2) หรือ None"""
    state = get_state()
    p1 = state["programs"]["p1"]
    p2 = state["programs"]["p2"]
    if p1 and p2:
        return p1, p2
    return None


def set_serial_info(port=None, connected=None):
    """อัพเดทข้อมูล serial connection"""
    state = get_state()
    if port is not None:
        state["serial"]["last_port"] = port
    if connected is not None:
        state["serial"]["connected"] = connected
    save_state()


def get_device_state():
    """คืนค่าสถานะอุปกรณ์"""
    state = get_state()
    return state["devices"].copy()


def increment_error_count():
    """เพิ่มตัวนับข้อผิดพลาด"""
    state = get_state()
    state["counters"]["total_errors"] += 1
    global _dirty
    _dirty = True


def save_if_dirty():
    """บันทึกเฉพาะเมื่อมีการเปลี่ยนแปลง — เรียกจาก periodic task"""
    if _dirty:
        save_state()
