import os
import logging
import json
import functools
from .singleton import Singleton

LEVEL_MAPPING = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _has_handler(logger: logging.Logger, handler_type: type) -> bool:
    return any(isinstance(h, handler_type) for h in logger.handlers)


class GoogelCustomLogger:
    """Google Cloud Functions用のシンプルなカスタムロガー"""

    def __init__(self, name="main"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        self.logger.propagate = False

        # メッセージのみ(フォーマットなし)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        # すでにハンドラがある場合は追加しない
        is_log_off = os.getenv("PENGENT_LOG_OFF", "").lower() == "true"
        if not is_log_off and not _has_handler(self.logger, logging.StreamHandler):
            self.logger.addHandler(handler)

    def _log(self, message, level="INFO", **fields):
        payload = {"serverity": level, "message": f"{message}", **fields}
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, message, **fields):
        self._log(message, level="INFO", **fields)

    def warning(self, message, **fields):
        self._log(message, level="WARNING", **fields)

    def error(self, message, **fields):
        self._log(message, level="ERROR", **fields)

    def exception(self, message, **fields):
        payload = {"serverity": "ERROR", "message": f"{message}", **fields}
        self.logger.info(json.dumps(payload, ensure_ascii=False), exc_info=True)

    def debug(self, message, **fields):
        self._log(message, level="DEBUG", **fields)

    def setLevel(self, level):
        self.logger.setLevel(level)


class CustomLogger(Singleton):
    """
    Singleton logger class that initializes a logger with a specified name
    and log file.It provides a method to log entry and exit of functions.
    """

    _initialized = False

    def __init__(self, name="pengent", log_file=None, level=None):
        if hasattr(self, "_initialized") and self._initialized:
            return  # すでに初期化済みなら何もしない

        if os.getenv("ENV", "local") == "local":
            if level is None and os.getenv("LOG_LEVEL"):
                level_str = os.getenv("LOG_LEVEL").upper()
                _level = LEVEL_MAPPING.get(level_str, logging.INFO)
            elif level is None:
                _level = logging.INFO
            else:
                _level = level

            self.logger = logging.getLogger(name)
            self.logger.setLevel(_level)
            self.logger.propagate = False

            # すでにハンドラがある場合は追加しない
            is_log_off = os.getenv("PENGENT_LOG_OFF", "").lower() == "true"
            if not is_log_off and not _has_handler(self.logger, logging.StreamHandler):
                formatter = logging.Formatter(
                    "%(asctime)s %(levelname)s "
                    "[%(name)s][%(filename)s:%(lineno)3d]: %(message)s"
                )

                # Console handler
                ch = logging.StreamHandler()
                ch.setFormatter(formatter)
                self.logger.addHandler(ch)

                # File handler
                if log_file:
                    fh = logging.FileHandler(log_file, encoding="utf-8")
                    fh.setFormatter(formatter)
                    self.logger.addHandler(fh)

            self._initialized = True
        elif os.getenv("ENV") in ["dev", "prd"]:
            self.logger = GoogelCustomLogger(name)
            self._initialized = True

    def get_logger(self):
        return self.logger

    def log_entry_exit(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.info(f"Enter: {func.__qualname__}")
            result = func(*args, **kwargs)
            self.logger.info(f"Exit: {func.__qualname__}")
            return result

        return wrapper


def get_logger(name="pengent", log_file=None, level=None):
    custom_logger = CustomLogger(name, log_file, level)
    return custom_logger.get_logger()
