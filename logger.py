# logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Папка для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Путь к файлу
LOG_FILE = LOG_DIR / "bot.log"

# Создаём логгер
logger = logging.getLogger("dr_halimova_bot")
logger.setLevel(logging.DEBUG)  # Записываем всё от DEBUG и выше

# Формат
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Ротирующий файловый хендлер (макс. 5 файлов по 10 МБ)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Консольный хендлер (только WARNING+ в продакшене, но DEBUG при разработке)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # или DEBUG — как удобно
console_handler.setFormatter(formatter)

# Добавляем хендлеры
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Отключаем пропагацию в root (чтобы не дублировались логи)
logger.propagate = False

# Экспорт
__all__ = ["logger"]