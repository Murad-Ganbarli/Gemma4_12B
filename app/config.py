import logging

# 1. Setup File Logger
logger = logging.getLogger("LocalServer")
logger.setLevel(logging.INFO)
logger.handlers = []

log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler("server.log", mode="a", encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# 2. Console Helper
class Console:
    @staticmethod
    def warn(message: str):
        print(f"\033[93m[WARNING] {message}\033[0m")

    @staticmethod
    def info(message: str):
        print(f"\033[94m[INFO] {message}\033[0m")

    @staticmethod
    def success(message: str):
        print(f"\033[92m[SUCCESS] {message}\033[0m")

    @staticmethod
    def error(message: str):
        print(f"\033[91m[ERROR] {message}\033[0m")