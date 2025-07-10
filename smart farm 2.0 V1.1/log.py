import logging

def setup_logger():
    logger = logging.getLogger("greenhouse_logger")
    if not logger.handlers:
        # เขียนลงไฟล์
        file_handler = logging.FileHandler("log.txt", encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
        file_handler.setFormatter(formatter)

        # แสดงผลบนหน้าจอ (console)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    return logger
