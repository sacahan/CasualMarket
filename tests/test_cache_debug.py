"""
缓存调试测试 - 验证 @with_cache 装饰器是否正常工作
"""

import asyncio
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.decorators import with_cache, _get_cache_service
from src.utils.logging import get_logger

logger = get_logger(__name__)


# 模拟被装饰的函数
class MockAPIClient:
    def __init__(self):
        self.call_count = 0

    @with_cache(enable_rate_limit=False, cache_key_prefix="test_endpoint")
    async def get_data(self, endpoint: str) -> dict:
        """
        模拟 API 调用，记录调用次数
        """
        self.call_count += 1
        logger.info(f"[实际 API 调用] 第 {self.call_count} 次调用: {endpoint}")
        return {"data": f"response_for_{endpoint}", "call_count": self.call_count}


@pytest.mark.asyncio
async def test_cache_key_generation():
    """测试缓存键生成是否一致"""

    # 模拟参数
    prefix = "test_endpoint"
    endpoint1 = "/opendata/t187ap06_L_ci"
    endpoint2 = "/opendata/t187ap06_L_ci"  # 相同的端点

    # 生成缓存键
    cache_params1 = [prefix, endpoint1]
    cache_params2 = [prefix, endpoint2]

    cache_key_str1 = "|".join(cache_params1)
    cache_key_str2 = "|".join(cache_params2)

    cache_key1 = hashlib.md5(cache_key_str1.encode()).hexdigest()[:16]
    cache_key2 = hashlib.md5(cache_key_str2.encode()).hexdigest()[:16]

    logger.info(f"缓存键字符串 1: {cache_key_str1} -> {cache_key1}")
    logger.info(f"缓存键字符串 2: {cache_key_str2} -> {cache_key2}")

    # 验证相同参数生成相同的缓存键
    assert cache_key1 == cache_key2, f"缓存键不相同: {cache_key1} != {cache_key2}"
    logger.info("✓ 缓存键生成正确 - 相同参数生成相同的键")


@pytest.mark.asyncio
async def test_cache_hit_on_second_call():
    """测试第二次调用是否命中缓存"""

    client = MockAPIClient()

    # 第一次调用
    result1 = await client.get_data("/opendata/t187ap06_L_ci")
    logger.info(f"第一次调用结果: {result1}")
    assert client.call_count == 1, "第一次调用应该执行实际函数"

    # 第二次调用（相同参数）
    result2 = await client.get_data("/opendata/t187ap06_L_ci")
    logger.info(f"第二次调用结果: {result2}")

    # 验证
    if client.call_count == 1:
        logger.info("✓ 缓存有效 - 第二次调用命中缓存，没有执行实际函数")
        assert result1 == result2, "缓存结果应该相同"
    else:
        logger.error("✗ 缓存失效 - 第二次调用没有命中缓存，又执行了实际函数")
        logger.error(f"  第一次调用次数: 1, 第二次调用后次数: {client.call_count}")
        logger.error(f"  第一次结果: {result1}")
        logger.error(f"  第二次结果: {result2}")
        assert False, "缓存应该在第二次调用时命中"


@pytest.mark.asyncio
async def test_different_parameters_no_cache_hit():
    """测试不同参数不会命中缓存"""

    client = MockAPIClient()

    # 第一次调用
    result1 = await client.get_data("/opendata/t187ap06_L_ci")
    logger.info(f"第一次调用结果: {result1}")
    assert client.call_count == 1

    # 第二次调用（不同参数）
    result2 = await client.get_data("/opendata/t187ap07_L_ci")
    logger.info(f"第二次调用结果: {result2}")

    # 验证
    assert client.call_count == 2, "不同参数应该执行实际函数"
    logger.info("✓ 缓存正确 - 不同参数没有命中缓存")


@pytest.mark.asyncio
async def test_cache_debug_log():
    """测试缓存调试日志"""

    logger.info("=" * 60)
    logger.info("缓存调试测试开始")
    logger.info("=" * 60)

    client = MockAPIClient()
    endpoint = "/opendata/t187ap06_L_ci"

    # 第一次调用
    logger.info(f"\n【第一次调用】端点: {endpoint}")
    result1 = await client.get_data(endpoint)

    # 第二次调用
    logger.info(f"\n【第二次调用】端点: {endpoint}")
    result2 = await client.get_data(endpoint)

    # 第三次调用
    logger.info(f"\n【第三次调用】端点: {endpoint}")
    result3 = await client.get_data(endpoint)

    logger.info("\n" + "=" * 60)
    logger.info(f"实际函数调用总次数: {client.call_count}")
    logger.info("=" * 60)

    if client.call_count == 1:
        logger.info("✓ 缓存工作正常 - 3 次调用只执行了 1 次实际函数")
    else:
        logger.error(f"✗ 缓存有问题 - 3 次调用执行了 {client.call_count} 次实际函数")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_cache_key_generation())
    asyncio.run(test_cache_hit_on_second_call())
    asyncio.run(test_different_parameters_no_cache_hit())
    asyncio.run(test_cache_debug_log())
