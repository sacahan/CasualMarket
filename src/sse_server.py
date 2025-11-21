#!/usr/bin/env python3
"""
SSE (Server-Sent Events) HTTP server for MCP.

This module provides an HTTP interface for the MCP server using SSE for
streaming responses. Uses FastMCP's built-in SSE support via run_sse_async().
"""

import asyncio

from .server import mcp
from .utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def main():
    """Start the SSE server using FastMCP's built-in run_sse_async"""
    logger.info("Starting CasualMarket MCP Server with SSE support")
    logger.info("Server will be available at http://0.0.0.0:8000")
    logger.info("SSE endpoint: http://0.0.0.0:8000/sse")

    # Use FastMCP's official SSE runner
    # This handles all MCP protocol details automatically
    await mcp.run_sse_async(host="0.0.0.0", port=8000, log_level="info")


def run():
    """Synchronous wrapper to run the async main function"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
