# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Start development server**: `make dev` (uses LangGraph dev server with HTTP and Studio UI)
- **Start stdio MCP server**: `make local` (starts LangGraph server + stdio MCP server)
- **Run tests**: `make test` (runs pytest on tests/ directory, excludes trio backend)
- **Run specific test file**: `make test TEST_FILE=path/to/test`
- **Test MCP stdio server**: `make test_mcp` (tests stdio MCP functionality)
- **Watch tests**: `make test_watch`
- **Lint code**: `make lint` (runs ruff, mypy with strict mode)
- **Format code**: `make format` (runs ruff format and import sorting)
- **Check spelling**: `make spell_check`

## Architecture Overview

This is a LangGraph-based web research agent that uses Google Gemini models and Google Search API to perform multi-step research. The system supports dual deployment modes: LangGraph development server (HTTP + Studio UI) and stdio MCP server for client integration.

### Core Components

- **LangGraph Agent** (`src/gemini_deepsearch_mcp/agent/graph.py`): State-driven research workflow with nodes for query generation, web research, reflection, and answer synthesis
- **FastMCP HTTP Server** (`src/gemini_deepsearch_mcp/app.py`): HTTP API that exposes the `deep_search` tool with configurable effort levels
- **FastMCP stdio Server** (`src/gemini_deepsearch_mcp/main.py`): Core stdio MCP server implementation with deep_search tool
- **Root stdio Entry Point** (`main.py`): Wrapper script that imports and runs the stdio MCP server from the main package
- **State Management** (`src/gemini_deepsearch_mcp/agent/state.py`): TypedDict-based states for different workflow stages

### Research Flow

1. **Query Generation**: Generates multiple search queries from user input
2. **Web Research**: Parallel execution of searches using Google Search API
3. **Reflection**: Analyzes results to identify knowledge gaps
4. **Iteration**: Continues research loops based on effort level and sufficiency
5. **Answer Synthesis**: Produces final citation-rich response

### Configuration

- LangGraph configuration in `langgraph.json` defines graph location and HTTP app
- Environment variables required: `GEMINI_API_KEY`
- Effort levels control research depth:
  - Low: 1 query, 1 loop, Flash model
  - Medium: 3 queries, 2 loops, Flash model  
  - High: 5 queries, 3 loops, Pro model

### Deployment Modes

1. **Development Mode** (`make dev`): LangGraph server with HTTP API and Studio UI for development
2. **stdio MCP Mode** (`make local`): Programmatically starts LangGraph server + stdio MCP server for client integration

### Key Files

- `src/gemini_deepsearch_mcp/agent/graph.py`: Main LangGraph workflow definition
- `src/gemini_deepsearch_mcp/app.py`: FastMCP HTTP server with deep_search tool  
- `src/gemini_deepsearch_mcp/main.py`: Core stdio MCP server implementation
- `main.py`: Root entry point wrapper for stdio MCP server (imports from src/gemini_deepsearch_mcp/main.py)
- `src/gemini_deepsearch_mcp/agent/configuration.py`: Agent configuration schema
- `src/gemini_deepsearch_mcp/agent/prompts.py`: Prompt templates for different workflow stages
- `src/gemini_deepsearch_mcp/agent/tools_and_schemas.py`: Pydantic schemas for structured outputs
- `tests/test_app.py`: Unit tests for FastMCP HTTP server and deep_search tool
- `tests/test_simple_mcp.py`: Basic tests for stdio MCP server import and startup
- `tests/test_stdio_client.py`: Integration test client for MCP stdio protocol

### Testing

The test suite includes comprehensive coverage of the MCP server functionality:

- **Unit Tests** (`tests/test_app.py`): Test deep_search tool with different effort levels, error handling, and FastAPI integration
- **Integration Tests** (`tests/test_simple_mcp.py`, `tests/test_stdio_client.py`): Test MCP stdio server startup, protocol compliance, and basic functionality
- **Test Configuration**: Tests use asyncio backend only (trio excluded due to missing dependencies)
- **Mock Support**: Tests use proper mocking for graph.invoke calls to avoid requiring GEMINI_API_KEY during testing

### Project Structure

```
├── main.py                                    # Root stdio MCP server entry point
├── src/gemini_deepsearch_mcp/                # Main package
│   ├── __init__.py
│   ├── main.py                               # Core stdio MCP server implementation
│   ├── app.py                                # FastMCP HTTP server
│   └── agent/                                # LangGraph agent components
│       ├── __init__.py
│       ├── graph.py                          # Main workflow definition
│       ├── configuration.py                 # Configuration schema
│       ├── prompts.py                        # Prompt templates
│       ├── state.py                          # State management
│       ├── tools_and_schemas.py              # Pydantic schemas
│       └── utils.py                          # Utility functions
├── tests/                                    # Test suite
│   ├── test_app.py                           # HTTP server tests
│   ├── test_simple_mcp.py                    # Basic MCP tests
│   └── test_stdio_client.py                 # Integration tests
├── langgraph.json                            # LangGraph configuration
└── pyproject.toml                            # Project configuration
```