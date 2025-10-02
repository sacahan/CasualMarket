"""
工具裝飾器 - 提供工具註冊和 MCP 整合功能
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastmcp import FastMCP

from ...utils.logging import get_logger

logger = get_logger(__name__)


def tool_decorator(
    mcp_instance: FastMCP,
    tool_name: str,
    description: str = "",
):
    """
    工具裝飾器，用於將工具類別的方法註冊為 MCP 工具。

    Args:
        mcp_instance: FastMCP 實例
        tool_name: MCP 工具名稱
        description: 工具描述

    Returns:
        裝飾器函數
    """

    def decorator(tool_class_method: Callable) -> Callable:
        @wraps(tool_class_method)
        async def wrapper(*args, **kwargs) -> dict[str, Any]:
            """MCP 工具包裝函數。"""
            # 創建工具實例（假設工具類別的第一個參數是 self）
            if args and hasattr(args[0], "safe_execute"):
                # 這是工具類別的方法
                tool_instance = args[0]
                result = await tool_instance.safe_execute(**kwargs)
            else:
                # 這是靜態函數，直接執行
                result = await tool_class_method(*args, **kwargs)

            return result

        # 註冊為 MCP 工具
        mcp_tool = mcp_instance.tool(wrapper)
        mcp_tool.__name__ = tool_name
        if description:
            mcp_tool.__doc__ = description

        logger.info(f"已註冊 MCP 工具: {tool_name}")
        return mcp_tool

    return decorator


def register_tool_class(
    mcp_instance: FastMCP, tool_class: type, method_mappings: dict[str, dict[str, str]]
):
    """
    註冊工具類別的多個方法為 MCP 工具。

    Args:
        mcp_instance: FastMCP 實例
        tool_class: 工具類別
        method_mappings: 方法映射，格式：
            {
                "method_name": {
                    "mcp_name": "MCP工具名稱",
                    "description": "工具描述"
                }
            }
    """
    # 創建工具實例
    tool_instance = tool_class()

    for method_name, config in method_mappings.items():
        if hasattr(tool_instance, method_name):
            method = getattr(tool_instance, method_name)
            mcp_name = config["mcp_name"]
            description = config.get("description", "")

            # 創建 MCP 工具函數
            @wraps(method)
            async def mcp_tool_func(*args, **kwargs):
                return await method(*args, **kwargs)

            # 設定工具名稱和描述
            mcp_tool_func.__name__ = mcp_name
            if description:
                mcp_tool_func.__doc__ = description

            # 註冊為 MCP 工具
            mcp_instance.tool(mcp_tool_func)
            logger.info(
                f"已註冊工具類別方法: {tool_class.__name__}.{method_name} -> {mcp_name}"
            )

        else:
            logger.warning(f"工具類別 {tool_class.__name__} 沒有方法 {method_name}")
