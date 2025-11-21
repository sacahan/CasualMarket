#!/usr/bin/env python
"""API 缓存诊断工具 - 快速识别缓存问题"""

import hashlib
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def generate_cache_key(func_name: str, prefix: str | None, endpoint: str) -> str:
    """
    模拟 @with_cache 装饰器的缓存键生成
    """
    cache_key_prefix = prefix or func_name
    cache_params = [cache_key_prefix, endpoint]
    cache_key_str = "|".join(cache_params)
    cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()[:16]

    return cache_key, cache_key_str


def diagnose_cache_consistency():
    """
    诊断缓存键一致性
    """
    logger.info("=" * 70)
    logger.info("【缓存键一致性诊断】")
    logger.info("=" * 70)

    # 模拟两次相同的调用
    calls = [
        ("get_data", None, "/opendata/t187ap06_L_ci"),
        ("get_data", None, "/opendata/t187ap06_L_ci"),  # 相同调用
        ("get_data", None, "/opendata/t187ap07_L_ci"),  # 不同端点
    ]

    results = {}
    for i, (func_name, prefix, endpoint) in enumerate(calls, 1):
        cache_key, cache_key_str = generate_cache_key(func_name, prefix, endpoint)

        logger.info(f"\n【调用 #{i}】")
        logger.info(f"  函数: {func_name}")
        logger.info(f"  前缀: {prefix or '(未指定，使用函数名)'}")
        logger.info(f"  端点: {endpoint}")
        logger.info(f"  缓存键字符串: {cache_key_str}")
        logger.info(f"  缓存键 (MD5[:16]): {cache_key}")

        # 存储结果用于对比
        key = (func_name, endpoint)
        if key not in results:
            results[key] = []
        results[key].append(cache_key)

    # 分析结果
    logger.info("\n" + "=" * 70)
    logger.info("【分析结果】")
    logger.info("=" * 70)

    for (func_name, endpoint), keys in results.items():
        if len(keys) == 1:
            logger.info(f"✓ {func_name}({endpoint}): 只调用 1 次")
        else:
            if all(k == keys[0] for k in keys):
                logger.info(
                    f"✓ {func_name}({endpoint}): "
                    f"{len(keys)} 次调用生成相同的缓存键 ({keys[0]}) "
                    f"→【应该命中缓存】✓"
                )
            else:
                logger.error(
                    f"✗ {func_name}({endpoint}): {len(keys)} 次调用生成不同的缓存键!"
                )
                for i, k in enumerate(keys, 1):
                    logger.error(f"    第 {i} 次: {k}")


def diagnose_parameter_formatting():
    """
    诊断参数格式问题
    """
    logger.info("\n" + "=" * 70)
    logger.info("【参数格式问题诊断】")
    logger.info("=" * 70)

    # 测试可能导致缓存键不同的情况
    test_cases = [
        ("正常", "/opendata/t187ap06_L_ci"),
        ("末尾空格", "/opendata/t187ap06_L_ci "),
        ("首部空格", " /opendata/t187ap06_L_ci"),
        ("大小写差异", "/opendata/t187ap06_l_ci"),
        ("None 值", None),
    ]

    logger.info("\n检查参数格式变化如何影响缓存键:")

    base_key = None
    for desc, endpoint in test_cases:
        if endpoint is None:
            logger.warning(f"  [{desc}] endpoint=None → 会导致错误!")
            continue

        cache_key, cache_key_str = generate_cache_key("get_data", None, endpoint)

        if base_key is None:
            base_key = cache_key
            logger.info(f"  [{desc}] {cache_key}")
        else:
            if cache_key == base_key:
                logger.info(f"  [{desc}] {cache_key} ✓ 相同")
            else:
                logger.error(f"  [{desc}] {cache_key} ✗ 不同! (vs. {base_key})")


def diagnose_common_issues():
    """
    诊断常见问题
    """
    logger.info("\n" + "=" * 70)
    logger.info("【常见问题检查清单】")
    logger.info("=" * 70)

    issues = [
        (
            "缓存 TTL 设置",
            "检查 MARKET_MCP_CACHE_TTL 环境变量",
            f"当前值: {__import__('os').getenv('MARKET_MCP_CACHE_TTL', '默认 1800s')}",
        ),
        (
            "缓存最大大小",
            "检查 MARKET_MCP_CACHE_MAX_SIZE 环境变量",
            f"当前值: {__import__('os').getenv('MARKET_MCP_CACHE_MAX_SIZE', '默认 1000')}",
        ),
        (
            "缓存最大内存",
            "检查 MARKET_MCP_CACHE_MAX_MEMORY_MB 环境变量",
            f"当前值: {__import__('os').getenv('MARKET_MCP_CACHE_MAX_MEMORY_MB', '默认 200.0 MB')}",
        ),
        (
            "缓存启用状态",
            "检查 MARKET_MCP_CACHING_ENABLED 环境变量",
            f"当前值: {__import__('os').getenv('MARKET_MCP_CACHING_ENABLED', '默认 true')}",
        ),
        (
            "日志级别",
            "建议设置为 DEBUG 以查看详细缓存日志",
            f"当前值: {__import__('os').getenv('LOG_LEVEL', '默认 INFO')}",
        ),
    ]

    for i, (issue, action, current) in enumerate(issues, 1):
        logger.info(f"\n[{i}] {issue}")
        logger.info(f"    操作: {action}")
        logger.info(f"    {current}")


def main():
    """主诊断流程"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 20 + "API 缓存诊断工具" + " " * 34 + "║")
    logger.info("╚" + "=" * 68 + "╝")

    diagnose_cache_consistency()
    diagnose_parameter_formatting()
    diagnose_common_issues()

    logger.info("\n" + "=" * 70)
    logger.info("【快速修复建议】")
    logger.info("=" * 70)
    logger.info("""
1. 启用 DEBUG 日志，重新运行工具两次查看详细缓存日志
   - 检查 "缓存键字符串" 是否完全相同
   - 检查是否看到 "[✓ API 快取命中]" 日志

2. 如果看到不同的缓存键，检查：
   - endpoint 参数是否有隐藏的空格或格式差异
   - 在代码中添加 .strip() 规范化参数

3. 如果缓存键相同但仍未命中，检查：
   - 缓存 TTL 设置是否过短
   - 缓存内存是否已满
   - 运行 `./scripts/docker-run.sh test` 检查完整日志

4. 完整诊断运行所有日志级别为 DEBUG 的测试：
   - LOG_LEVEL=DEBUG ./scripts/docker-run.sh test
    """)

    logger.info("=" * 70)
    logger.info("诊断完成!")
    logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    main()
