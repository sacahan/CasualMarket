"""
工具基類 - 提供統一的工具介面和錯誤處理
"""

from abc import ABC, abstractmethod
from typing import Any

from ...api.openapi_client import OpenAPIClient
from ...api.twse_client import create_client
from ...utils.logging import get_logger


class ToolBase(ABC):
    """
    所有工具的基類，提供統一的介面和錯誤處理。
    """

    def __init__(self, name: str):
        """
        初始化工具基類。

        Args:
            name: 工具名稱
        """
        self.name = name
        self.logger = get_logger(f"tools.{name}")

        # 初始化 API 客戶端
        self.api_client = OpenAPIClient()
        self.stock_client = create_client()

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        執行工具的主要功能。

        Args:
            **kwargs: 工具參數

        Returns:
            統一格式的回應字典
        """
        pass

    def _success_response(self, data: Any, **metadata) -> dict[str, Any]:
        """
        建立成功回應。

        Args:
            data: 回應資料
            **metadata: 額外的元資料

        Returns:
            成功回應字典
        """
        response = {
            "success": True,
            "data": data,
            "tool": self.name,
        }
        response.update(metadata)
        return response

    def _error_response(self, error: str, **metadata) -> dict[str, Any]:
        """
        建立錯誤回應。

        Args:
            error: 錯誤訊息
            **metadata: 額外的元資料

        Returns:
            錯誤回應字典
        """
        response = {
            "success": False,
            "error": error,
            "tool": self.name,
        }
        response.update(metadata)
        return response

    async def safe_execute(self, **kwargs) -> dict[str, Any]:
        """
        安全執行工具，包含錯誤處理。

        Args:
            **kwargs: 工具參數

        Returns:
            執行結果
        """
        try:
            self.logger.info(f"執行工具 {self.name}")
            result = await self.execute(**kwargs)

            if result.get("success", False):
                self.logger.info(f"工具 {self.name} 執行成功")
            else:
                self.logger.warning(
                    f"工具 {self.name} 執行失敗: {result.get('error', 'Unknown error')}"
                )

            return result

        except Exception as e:
            error_msg = f"工具 {self.name} 執行異常: {str(e)}"
            self.logger.error(error_msg)
            return self._error_response(error_msg)

    def close(self):
        """關閉資源。"""
        if hasattr(self, "api_client"):
            self.api_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
