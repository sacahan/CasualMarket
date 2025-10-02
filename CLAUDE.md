# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CasualMarket is a Taiwan Stock Exchange MCP (Model Context Protocol) Server that provides real-time stock price queries for Taiwan securities. It uses FastMCP framework for simplified MCP tool registration and includes intelligent rate limiting, caching, and financial analysis features.

## Development Commands

### Server Execution

```bash
# Run the MCP server locally (primary method)
uvx --from . casual-market-mcp

# Alternative development execution
uv run python src/main.py
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
5. **Financial Tools** (`src/tools/analysis/`): Advanced financial analysis using TWSE OpenAPI
6. **Data Models** (`src/models/`): Pydantic models for stock data, trading operations, and API responses
7. **Scrapers** (`src/scrapers/`): TWSE data scrapers for maintaining the securities database

### Key Architectural Patterns

- **FastMCP Integration**: Uses `@mcp.tool` decorators instead of traditional MCP server setup
- **Decorator-Based Enhancement**: Function decorators (`@with_cache`) add caching and rate limiting to API methods
- **Rate Limited Caching**: All API calls go through `RateLimitedCacheService` to prevent API abuse
- **Layered Validation**: Input validation at multiple levels (symbol format, market type, API response)
- **Company Name Resolution**: Supports both stock codes and company names via local SQLite database
- **Modular Tool Design**: Financial analysis tools are pluggable components using dependency injection

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

- `MARKET_MCP_API_TIMEOUT`: API request timeout (default: 10s)
- `MARKET_MCP_API_RETRIES`: Retry attempts (default: 5)
- `MARKET_MCP_TWSE_API_URL`: TWSE API endpoint URL
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

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
- Maintain high test coverage (current target: >80%)

### Database Management

- **Securities Database**: `src/twse_securities.db` contains ISIN codes and company name mappings
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
