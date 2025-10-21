"""
Dynamic configuration manager for rate limiting and cache parameters.
Allows runtime adjustment of system parameters for optimal performance.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Thread-safe configuration manager for dynamic parameter adjustment.
    Supports runtime updates and configuration persistence.
    """

    def __init__(self, config_file: str | None = None):
        self.config_file = Path(config_file) if config_file else None
        self.lock = threading.RLock()

        # Default configuration
        self._config = {
            "rate_limiting": {
                "per_stock_interval_seconds": 30.0,
                "global_limit_per_minute": 20,
                "per_second_limit": 2,
                "enabled": True,
            },
            "caching": {
                "ttl_seconds": 30,
                "max_size": 1000,
                "max_memory_mb": 200.0,
                "enabled": True,
            },
            "api": {
                "base_url": "https://www.twse.com.tw",
                "timeout_seconds": 10.0,
                "retry_attempts": 3,
                "retry_delay_seconds": 1.0,
            },
            "monitoring": {
                "stats_retention_hours": 24,
                "performance_threshold_ms": 5000.0,
                "cache_hit_rate_target_percent": 80.0,
                "enable_detailed_logging": False,
            },
        }

        # Load configuration from file if it exists
        self.load_config()

    def load_config(self) -> bool:
        """Load configuration from file. Returns True if successful."""
        if not self.config_file or not self.config_file.exists():
            logger.info("找不到設定檔案，使用預設值")
            return False

        try:
            with self.lock:
                with open(self.config_file, encoding="utf-8") as f:
                    file_config = json.load(f)

                # Merge with defaults (file config takes precedence)
                self._merge_config(self._config, file_config)

                logger.info(f"從 {self.config_file} 載入設定檔")
                return True
        except Exception as e:
            logger.error(f"載入設定檔失敗 {self.config_file}: {e}")
            return False

    def save_config(self) -> bool:
        """Save current configuration to file. Returns True if successful."""
        if not self.config_file:
            logger.warning("未指定設定檔路徑")
            return False

        try:
            with self.lock:
                # Create directory if it doesn't exist
                self.config_file.parent.mkdir(parents=True, exist_ok=True)

                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)

                logger.info(f"設定檔已儲存至 {self.config_file}")
                return True
        except Exception as e:
            logger.error(f"儲存設定檔失敗 {self.config_file}: {e}")
            return False

    def _merge_config(self, target: dict, source: dict) -> None:
        """
        遞迴合併源配置到目標配置。
        
        邏輯：
        - 如果鍵值指向字典，遞迴合併
        - 否則直接覆蓋目標值（源配置優先級更高）
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                # 遞迴合併嵌套字典
                self._merge_config(target[key], value)
            else:
                # 直接覆蓋：源配置的值優先
                target[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        使用點符號表示法取得配置值。
        
        示例：
            get('rate_limiting.per_stock_interval_seconds')
            get('caching.ttl_seconds')
        
        Args:
            key_path: 以點分隔的鍵路徑
            default: 如果鍵不存在則返回的預設值
        
        Returns:
            配置值或預設值
        """
        with self.lock:
            # 將路徑分割為層級鍵
            keys = key_path.split(".")
            value = self._config

            try:
                # 逐層導航到目標值
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                logger.debug(f"找不到設定鍵值 '{key_path}'，回傳預設值")
                return default

    def set(self, key_path: str, value: Any, save_to_file: bool = False) -> bool:
        """
        使用點符號表示法設定配置值。
        
        示例：
            set('rate_limiting.per_stock_interval_seconds', 30.0)
            set('caching.ttl_seconds', 60, save_to_file=True)
        
        Args:
            key_path: 以點分隔的鍵路徑
            value: 要設定的值
            save_to_file: 是否持久化到檔案
        
        Returns:
            True 如果設定成功
        """
        with self.lock:
            keys = key_path.split(".")
            config = self._config

            try:
                # 逐層導航到目標鍵的父級，建立必要的中間層級
                for key in keys[:-1]:
                    if key not in config:
                        config[key] = {}
                    config = config[key]

                # 設定最終的值
                config[keys[-1]] = value

                logger.info(f"設定已更新: {key_path} = {value}")

                # 可選：同步保存到檔案
                if save_to_file:
                    return self.save_config()

                return True
            except Exception as e:
                logger.error(f"設定配置失敗 {key_path}: {e}")
                return False

    def get_rate_limiting_config(self) -> dict[str, Any]:
        """Get rate limiting configuration."""
        with self.lock:
            return self._config.get("rate_limiting", {}).copy()

    def get_caching_config(self) -> dict[str, Any]:
        """Get caching configuration."""
        with self.lock:
            return self._config.get("caching", {}).copy()

    def get_api_config(self) -> dict[str, Any]:
        """Get API configuration."""
        with self.lock:
            return self._config.get("api", {}).copy()

    def get_monitoring_config(self) -> dict[str, Any]:
        """Get monitoring configuration."""
        with self.lock:
            return self._config.get("monitoring", {}).copy()

    def update_rate_limits(
        self,
        per_stock_interval: float | None = None,
        global_limit_per_minute: int | None = None,
        per_second_limit: int | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """
        批量更新限速配置參數。
        
        允許同時更新多個限速參數。只有非 None 的參數才會被更新。
        
        Args:
            per_stock_interval: 單個股票的限速間隔（秒）
            global_limit_per_minute: 全域每分鐘限制（請求數）
            per_second_limit: 每秒限制（請求數）
            save_to_file: 是否持久化變更到檔案
        
        Returns:
            True 如果更新成功
        """
        try:
            with self.lock:
                # 只更新提供的（非 None）參數
                if per_stock_interval is not None:
                    self._config["rate_limiting"][
                        "per_stock_interval_seconds"
                    ] = per_stock_interval

                if global_limit_per_minute is not None:
                    self._config["rate_limiting"][
                        "global_limit_per_minute"
                    ] = global_limit_per_minute

                if per_second_limit is not None:
                    self._config["rate_limiting"]["per_second_limit"] = per_second_limit

                logger.info("流量限制設定已更新")

                # 可選：保存到檔案以確保下次啟動時載入更新的配置
                if save_to_file:
                    return self.save_config()

                return True
        except Exception as e:
            logger.error(f"更新流量限制設定失敗: {e}")
            return False

    def update_cache_settings(
        self,
        ttl_seconds: int | None = None,
        max_size: int | None = None,
        max_memory_mb: float | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update cache configuration."""
        try:
            with self.lock:
                if ttl_seconds is not None:
                    self._config["caching"]["ttl_seconds"] = ttl_seconds

                if max_size is not None:
                    self._config["caching"]["max_size"] = max_size

                if max_memory_mb is not None:
                    self._config["caching"]["max_memory_mb"] = max_memory_mb

                logger.info("快取設定已更新")

                if save_to_file:
                    return self.save_config()

                return True
        except Exception as e:
            logger.error(f"更新快取設定失敗: {e}")
            return False

    def is_rate_limiting_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.get("rate_limiting.enabled", True)

    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.get("caching.enabled", True)

    def enable_feature(self, feature: str, save_to_file: bool = False) -> bool:
        """Enable a feature (rate_limiting or caching)."""
        return self.set(f"{feature}.enabled", True, save_to_file)

    def disable_feature(self, feature: str, save_to_file: bool = False) -> bool:
        """Disable a feature (rate_limiting or caching)."""
        return self.set(f"{feature}.enabled", False, save_to_file)

    def get_all_config(self) -> dict[str, Any]:
        """Get a copy of the entire configuration."""
        with self.lock:
            return json.loads(json.dumps(self._config))  # Deep copy

    def reset_to_defaults(self, save_to_file: bool = False) -> bool:
        """Reset configuration to default values."""
        try:
            with self.lock:
                self._config = {
                    "rate_limiting": {
                        "per_stock_interval_seconds": 30.0,
                        "global_limit_per_minute": 20,
                        "per_second_limit": 2,
                        "enabled": True,
                    },
                    "caching": {
                        "ttl_seconds": 30,
                        "max_size": 1000,
                        "max_memory_mb": 200.0,
                        "enabled": True,
                    },
                    "api": {
                        "base_url": "https://www.twse.com.tw",
                        "timeout_seconds": 10.0,
                        "retry_attempts": 3,
                        "retry_delay_seconds": 1.0,
                    },
                    "monitoring": {
                        "stats_retention_hours": 24,
                        "performance_threshold_ms": 5000.0,
                        "cache_hit_rate_target_percent": 80.0,
                        "enable_detailed_logging": False,
                    },
                }

                logger.info("設定已重置為預設值")

                if save_to_file:
                    return self.save_config()

                return True
        except Exception as e:
            logger.error(f"重置設定失敗: {e}")
            return False
