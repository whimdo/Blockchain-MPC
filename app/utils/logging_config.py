from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _safe_log_name(name: str) -> str:
    return name.replace(".", "_").replace("/", "_").replace("\\", "_")


def get_logger(name: str) -> logging.Logger:
    """获取模块日志器，并写入单个模块日志文件。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    safe_name = _safe_log_name(name)
    log_path = LOG_DIR / f"{safe_name}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
