"""
error_report.py — ระบบรายงานข้อผิดพลาดแบบรวมศูนย์
Centralized error reporting: tracks errors, deduplicates, and provides safe execution wrappers.
"""

import os
import json
import time
import traceback
import functools
from datetime import datetime
from log import setup_logger

logger = setup_logger()

# ─── Config ───────────────────────────────────────────────────
ERROR_DIR = "log"
ERROR_FILE = os.path.join(ERROR_DIR, "errors.json")
MAX_ERRORS = 500  # จำนวนข้อผิดพลาดสูงสุดที่เก็บ

os.makedirs(ERROR_DIR, exist_ok=True)

# ─── In-memory error tracker ──────────────────────────────────
_error_counts = {}  # key = "module:message_hash" → count
_last_error_time = {}  # key → timestamp ของครั้งล่าสุดที่รายงาน
_DEDUP_WINDOW = 60  # วินาที — ไม่รายงานข้อผิดพลาดเดิมซ้ำภายในช่วงนี้

# ─── Serial health tracking ──────────────────────────────────
_serial_errors = 0
_serial_last_ok = time.time()
SERIAL_ERROR_THRESHOLD = 5  # จำนวนข้อผิดพลาด serial ก่อนแนะนำ reconnect


def _make_key(module, message):
    """สร้าง key สำหรับ deduplication"""
    # ใช้ 100 ตัวอักษรแรกของ message เป็น key
    short = message[:100] if message else "unknown"
    return f"{module}:{short}"


def report_error(module, error, context=""):
    """
    รายงานข้อผิดพลาดอย่างปลอดภัย — ไม่ crash ไม่ว่าจะเกิดอะไร
    
    Args:
        module: ชื่อโมดูลที่เกิดข้อผิดพลาด (เช่น "read_sensor_all")
        error: Exception object หรือ string
        context: ข้อมูลเพิ่มเติม (เช่น "ขณะอ่านค่า BME1")
    """
    try:
        msg = str(error)
        key = _make_key(module, msg)
        now = time.time()

        # Deduplication: ไม่รายงานซ้ำภายในช่วงเวลาที่กำหนด
        if key in _last_error_time:
            elapsed = now - _last_error_time[key]
            if elapsed < _DEDUP_WINDOW:
                _error_counts[key] = _error_counts.get(key, 1) + 1
                return  # ข้ามการรายงาน — ซ้ำเร็วเกินไป

        _last_error_time[key] = now
        count = _error_counts.pop(key, 0)

        # Log to console/file
        repeat_note = f" (ซ้ำ {count} ครั้งใน {_DEDUP_WINDOW}s)" if count > 0 else ""
        ctx_note = f" [{context}]" if context else ""
        logger.error(f"[{module}]{ctx_note} {msg}{repeat_note}")

        # Save to JSON error log
        _save_error_record(module, msg, context, count)

    except Exception:
        # error reporting ต้องไม่ crash ไม่ว่าจะเกิดอะไร
        pass


def _save_error_record(module, message, context, repeat_count):
    """บันทึก error record ลงไฟล์ JSON"""
    try:
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "module": module,
            "message": message,
            "context": context,
            "traceback": traceback.format_exc() if "NoneType" not in traceback.format_exc() else "",
            "repeat_count": repeat_count
        }

        # โหลดข้อมูลเดิม
        errors = []
        if os.path.exists(ERROR_FILE):
            try:
                with open(ERROR_FILE, "r", encoding="utf-8") as f:
                    errors = json.load(f)
                if not isinstance(errors, list):
                    errors = []
            except (json.JSONDecodeError, ValueError):
                errors = []

        errors.append(record)

        # จำกัดจำนวน
        if len(errors) > MAX_ERRORS:
            errors = errors[-MAX_ERRORS:]

        with open(ERROR_FILE, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)

    except Exception:
        pass  # การบันทึก error ต้องไม่ crash


def report_serial_error(error, context=""):
    """รายงาน serial error และติดตามสุขภาพการเชื่อมต่อ"""
    global _serial_errors
    _serial_errors += 1
    report_error("serial", error, context)


def report_serial_ok():
    """รายงานว่า serial ทำงานปกติ — reset error counter"""
    global _serial_errors, _serial_last_ok
    _serial_errors = 0
    _serial_last_ok = time.time()


def should_reconnect_serial():
    """ตรวจสอบว่าควร reconnect serial หรือไม่"""
    return _serial_errors >= SERIAL_ERROR_THRESHOLD


def get_serial_health():
    """คืนค่าสถานะสุขภาพของ serial connection"""
    return {
        "error_count": _serial_errors,
        "last_ok": datetime.fromtimestamp(_serial_last_ok).strftime("%H:%M:%S"),
        "needs_reconnect": should_reconnect_serial()
    }


def safe_execute(func=None, module=None, default=None, context=""):
    """
    Decorator / wrapper ที่จับ exception ทั้งหมดและรายงาน แทนที่จะ crash
    
    ใช้เป็น decorator:
        @safe_execute(module="fan_sys")
        def fan1_on(ser):
            ...
    
    ใช้เป็น function call:
        result = safe_execute(lambda: risky_function(), module="main", default=None)
    """
    if func is None:
        # ถูกเรียกเป็น decorator factory: @safe_execute(module="x")
        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    mod = module or fn.__module__ or fn.__name__
                    ctx = context or fn.__name__
                    report_error(mod, e, ctx)
                    return default
            return wrapper
        return decorator
    else:
        # ถูกเรียกเป็น function call: safe_execute(lambda: ..., module="x")
        try:
            return func()
        except Exception as e:
            report_error(module or "unknown", e, context)
            return default


def get_error_summary():
    """สรุปสถานะข้อผิดพลาดปัจจุบัน"""
    try:
        if not os.path.exists(ERROR_FILE):
            return {"total_errors": 0, "recent": []}

        with open(ERROR_FILE, "r", encoding="utf-8") as f:
            errors = json.load(f)

        return {
            "total_errors": len(errors),
            "recent": errors[-5:] if errors else [],
            "serial_health": get_serial_health()
        }
    except Exception:
        return {"total_errors": -1, "recent": [], "error": "ไม่สามารถอ่านไฟล์ error log"}
