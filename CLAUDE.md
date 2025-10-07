# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CasualMarket is a Taiwan Stock Exchange MCP (Model Context Protocol) Server that provides real-time stock price queries for Taiwan securities. It uses FastMCP framework for simplified MCP tool registration and includes intelligent rate limiting, caching, and financial analysis features.

## Development Commands

### Server Execution

#### Production Execution

```bash
# Production deployment (uses cached builds)
uvx --from . casual-market-mcp
```

#### Development Execution (Recommended for Active Development)

```bash
# Development mode - direct execution avoids uvx cache issues
uv run python -m src.main

# Quick functionality test
uv run python tests/api/demo_enhanced_client.py
```

#### Cache Management

```bash
# Clear uvx cache when needed (production deployment)
uv cache clean

# Development mode automatically uses latest code
# No cache clearing needed when using uv run
```

### Testing

```bash
# Run all tests with coverage
uv run pytest

# Run specific test categories
uv run pytest tests/api/           # API integration tests
uv run pytest tests/server/        # Server functionality tests
uv run pytest tests/mcp/           # MCP protocol tests
uv run pytest tests/tools/         # Tool functionality tests

# Run a single test file
uv run pytest tests/api/test_twse_standalone.py

# Generate coverage report
uv run pytest --cov=src --cov-report=html
```

#### Current Testing Status

**Overall Health**: ✅ Excellent (98% pass rate)

- **Total Test Cases**: 110
- **Passing Tests**: 108 (98%)
- **Skipped Tests**: 2 (2%)
- **Failed Tests**: 0 (0%)
- **Code Coverage**: 62%

**Test Categories**:

- ✅ **API Integration Tests** (`tests/api/`) - All passing, includes rate limiting and caching
- ✅ **Server Functionality** (`tests/server/`) - All core server features working
- ✅ **MCP Protocol Tests** (`tests/mcp/`) - Protocol compliance verified
- ✅ **Tool Functionality** (`tests/tools/`) - All tools fully tested and working
  - ✅ Foreign Investment Tools (12/12 passing)
  - ✅ Market Tools (13/13 passing)
  - ✅ Financial Tools (all passing)
  - ✅ Trading Tools (all passing)

**Recent Fixes**: Successfully resolved 19 failing test cases in foreign investment and market tools by:

- Correcting mock API method calls to match actual implementations
- Aligning test expectations with actual tool return formats
- Fixing parameter names and data structures
- Ensuring proper error message validation

### Code Quality

```bash
# Lint with ruff
uv run ruff check src/ tests/

# Type checking with mypy
uv run mypy src/

# Fix auto-fixable linting issues
uv run ruff check --fix src/ tests/
```

### Development Setup Verification

```bash
# Test uvx execution and MCP protocol
./tests/test_uvx_execution.sh

# Test specific enhanced client functionality
uv run python tests/api/demo_enhanced_client.py

# Debug API functionality
uv run python tests/api/debug_api.py
```

## Architecture Overview

### Core Components

1. **FastMCP Server** (`src/server.py`): Main MCP server using `@mcp.tool` decorators for simplified tool registration
2. **API Client Layer** (`src/api/`):
   - `twse_client.py`: Taiwan Stock Exchange API integration with decorator-based enhancements
   - `openapi_client.py`: TWSE OpenAPI integration for financial statements
   - `decorators.py`: Function decorators for adding caching and rate limiting to API methods
3. **Cache System** (`src/cache/`): Integrated rate limiting and caching service with request tracking
4. **Securities Database** (`src/securities_db.py`): SQLite database for ISIN codes and company name resolution
5. **Tool Base Architecture** (`src/tools/base/`): Base classes and decorators for standardized tool development
6. **Financial Tools** (`src/tools/`): Domain-organized tools including:
   - `trading/`: Stock prices, trading operations, statistics
   - `financial/`: Financial statements, dividends, valuation, revenue
   - `market/`: Market indices, ETF data, margin trading
   - `foreign/`: Foreign investment analysis
7. **Data Parser** (`src/parsers/twse_parser.py`): TWSE API response parsing and validation
8. **Data Models** (`src/models/`): Pydantic models for stock data, trading operations, and API responses
9. **Scrapers** (`src/scrapers/`): TWSE data scrapers for maintaining the securities database

### Key Architectural Patterns

- **FastMCP Integration**: Uses `@mcp.tool` decorators instead of traditional MCP server setup
- **ToolBase Inheritance**: All tools inherit from `ToolBase` class providing:
  - Unified error handling via `safe_execute()` method
  - Standard response formatting (`_success_response`, `_error_response`)
  - Built-in API client initialization (both TWSE and OpenAPI clients)
  - Context manager support for resource cleanup
- **Dual API Client Architecture**:
  - `TWStockAPIClient`: Real-time stock quotes from TWSE API (with rate limiting)
  - `OpenAPIClient`: Financial statements and company data from TWSE OpenAPI (typically no rate limiting)
- **Decorator-Based Enhancement**: Function decorators (`@with_cache`) add caching and rate limiting to API methods
- **Rate Limited Caching**: All API calls go through `RateLimitedCacheService` to prevent API abuse
- **Unified Response Model**: All tools return `MCPToolResponse[T]` with consistent structure
- **Layered Validation**: Input validation at multiple levels (symbol format, market type, API response)
- **Company Name Resolution**: Supports both stock codes and company names via local SQLite database
- **Data Parsing Pipeline**: `TWStockDataParser` transforms raw TWSE API JSON into validated models

### Data Flow

1. **Tool Request** → **Input Validation** → **Company Name Resolution** → **Cache Check** → **API Call** → **Response Parsing** → **Tool Response**
2. **Rate Limiting**: Enforced at cache service level before API calls
3. **Error Handling**: Graceful fallbacks with detailed error messages and client switching
4. **Database Integration**: Company names resolved to stock codes via local SQLite database before API calls

## Module Dependencies

### Critical Dependencies

- **FastMCP**: Core MCP framework for tool registration
- **HTTPX**: Async HTTP client for TWSE API calls
- **Pydantic**: Data validation and serialization
- **CacheTools**: In-memory caching implementation
- **Loguru**: Structured logging

### Development Dependencies

- **Pytest**: Testing framework with async support
- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking

## Configuration

### Environment Variables

所有配置都通過環境變數管理，支援 `.env` 文件。配置分為以下幾個類別：

#### API 客戶端配置

- `MARKET_MCP_API_TIMEOUT`: API 請求超時時間秒數 (預設: 10)
- `MARKET_MCP_API_RETRIES`: API 請求重試次數 (預設: 5)
- `MARKET_MCP_TWSE_API_URL`: 台灣證交所 API 端點 URL

#### 限速配置

- `MARKET_MCP_RATE_LIMIT_INTERVAL`: 每個股票請求間隔秒數 (預設: 30.0)
- `MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE`: 全域每分鐘請求限制 (預設: 20)
- `MARKET_MCP_RATE_LIMIT_PER_SECOND`: 每秒請求限制 (預設: 2)
- `MARKET_MCP_RATE_LIMITING_ENABLED`: 是否啟用限速功能 (預設: true)

#### 快取配置

- `MARKET_MCP_CACHE_TTL`: 快取存活時間秒數 (預設: 30)
- `MARKET_MCP_CACHE_MAX_SIZE`: 快取最大條目數 (預設: 1000)
- `MARKET_MCP_CACHE_MAX_MEMORY_MB`: 快取最大記憶體使用 MB (預設: 200.0)
- `MARKET_MCP_CACHING_ENABLED`: 是否啟用快取功能 (預設: true)

#### 監控配置

- `MARKET_MCP_MONITORING_STATS_RETENTION_HOURS`: 統計資料保留小時數 (預設: 24)
- `MARKET_MCP_MONITORING_CACHE_HIT_RATE_TARGET`: 快取命中率目標百分比 (預設: 80.0)

#### 日誌配置

- `MARKET_MCP_LOG_LEVEL`: 日誌級別 DEBUG/INFO/WARNING/ERROR (預設: INFO)
- `MARKET_MCP_LOG_FORMAT`: 日誌格式 (可選)
- `MARKET_MCP_LOG_FILE`: 日誌文件路徑 (可選)

### 配置文件

**設定方式**：

1. 複製範本：`cp .env.simple .env`
2. 修改 `.env` 中的值
3. `.env` 文件不會被 git 追蹤，可安全存放敏感資訊

**檔案說明**：

- `.env`: 實際配置文件（不被 git 追蹤）
- `.env.simple`: 配置範本文件（被 git 追蹤，不含敏感資訊）

### MCP Client Configuration

Example Claude Desktop configuration in `examples/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "casualtrader": {
      "command": "uvx",
      "args": ["--from", "/path/to/CasualMarket", "casual-market-mcp"]
    }
  }
}
```

## File Structure Notes

- **Source Code**: All implementation in `src/` directory
- **Package Structure**: Flat module structure, no nested `market_mcp` package
- **Entry Point**: `src/main.py` contains the main() function for uvx execution
- **Tools**: MCP tools defined directly in `src/server.py` using FastMCP decorators
- **Tests**: Comprehensive test suite in `tests/` with category-based organization

## Development Guidelines

### API Client Usage

- API methods are enhanced with `@with_cache` decorators for automatic caching and rate limiting
- Cache service is globally managed and automatically integrated - don't bypass it
- Handle both stock codes (2330) and company names ("台積電") in user inputs
- Company name resolution happens automatically via the securities database
- Use `force_refresh=True` parameter to bypass cache when needed

### Error Handling

- Return structured error responses with `status: "error"` field
- Include original user input in error responses for debugging
- Log errors at appropriate levels (INFO for expected failures, ERROR for system issues)

### Testing Strategy

- Test real API integration in `tests/api/` (includes rate limiting and decorator-based caching tests)
- Mock external dependencies for unit tests
- Use pytest-asyncio for async test cases
- Run the `test_uvx_execution.sh` script to verify MCP protocol compliance
- Test decorator functionality and cache behavior
- **Current Status**: 98% test pass rate (108/110 tests passing), 62% code coverage
- **Recently Fixed**: All foreign investment and market tools tests now pass completely
- Comprehensive test suite covering all major components and edge cases

### Database Management

- **Securities Database**: `src/data/twse_securities.db` contains ISIN codes and company name mappings
- **Database Updates**: Use scrapers in `src/scrapers/` to refresh company data
- **Company Name Resolution**: Handled automatically via `securities_db.py` module
- **Testing Database**: Isolated test database used during testing to avoid conflicts

### FastMCP Tool Development

- Use `@mcp.tool` decorator for new tools
- Include comprehensive docstrings for tool descriptions
- Return structured dictionaries with consistent `status` field
- Handle Taiwan-specific requirements (1000-share minimum trading units)
- Integrate with `FinancialAnalysisTool` for complex financial calculations

### Decorator Usage

- Use `@with_cache(cache_key_prefix, enable_rate_limit)` for API methods requiring caching
- Cache key prefix should be descriptive (e.g., "quote", "financial", "profile")
- Enable rate limiting for real-time data, disable for less frequent data sources
- Decorators handle global cache service initialization automatically

**Examples:**

```python
@with_cache("quote", enable_rate_limit=True)
async def get_stock_quote(self, symbol: str):
    # Real-time stock quotes need rate limiting
    pass

@with_cache("financial", enable_rate_limit=False)
async def get_financial_data(self, symbol: str):
    # Financial reports don't need rate limiting
    pass
```
