#!/usr/bin/env python
"""API 缓存诊断工具"""

import hashlib
import logging

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)


def generate_cache_key(func_name: str, endpoint: str) -> tuple:
    """生成缓存键"""
    cache_params = [func_name, endpoint]
    cache_key_str = "|".join(cache_params)
    cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()[:16]
    return cache_key, cache_key_str


def test_consistency():
    """测试相同调用是否生成相同缓存键"""
    logger.info("=" * 70)
    logger.info("【缓存键一致性测试】")
    logger.info("=" * 70)

    endpoint = "/opendata/t187ap06_L_ci"

    # 模拟3次相同调用
    keys = []
    for i in range(3):
        cache_key, cache_key_str = generate_cache_key("get_data", endpoint)
        keys.append(cache_key)
        logger.info(f"第 {i + 1} 次: {cache_key_str} → {cache_key}")

    logger.info("\n【结果】")
    if len(set(keys)) == 1:
        logger.info(f"✓ 3 次调用生成相同的缓存键: {keys[0]}")
        logger.info("  → 第 2 和 3 次调用应该命中缓存")
    else:
        logger.error(f"✗ 缓存键不一致: {set(keys)}")


if __name__ == "__main__":
    test_consistency()
