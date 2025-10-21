"""
Logging utilities for CasualTrader MCP Server.

This module provides structured logging using loguru with configuration
support for different environments and output formats.
"""

# 移除 config 依賴，直接使用環境變數
import os
import sys

from loguru import logger


def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
    format_string: str | None = None,
) -> None:
    """
    Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        format_string: Custom log format string
    """
    # Use provided values or fall back to environment variables
    log_level = level or os.getenv("MARKET_MCP_LOG_LEVEL", "INFO")
    log_format = format_string or os.getenv(
        "MARKET_MCP_LOG_FORMAT",
        "<green>{time}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}",
    )
    log_path = log_file or os.getenv("MARKET_MCP_LOG_FILE")

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler if specified
    if log_path:
        # 確保日誌目錄存在
        from pathlib import Path

        log_file_path = Path(log_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            level=log_level,
            format=log_format,
            rotation="1 day",
            retention="7 days",
            compression="gz",
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"日誌系統已初始化 - 層級: {log_level}")
    if log_path:
        logger.info(f"日誌檔案: {log_path}")


def get_logger(name: str):
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)
