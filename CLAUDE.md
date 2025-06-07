# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Start development server**: `make dev` (uses LangGraph dev server with HTTP and Studio UI)
- **Start stdio MCP server**: `make local` (starts LangGraph server + stdio MCP server)
- **Run tests**: `make test` or `uv run --with-editable . pytest tests/unit_tests/`
- **Run specific test file**: `make test TEST_FILE=path/to/test`
- **Test MCP stdio server**: `make test_mcp` (tests stdio MCP functionality)
- **Watch tests**: `make test_watch`
- **Lint code**: `make lint` (runs ruff, mypy with strict mode)
- **Format code**: `make format` (runs ruff format and import sorting)
- **Check spelling**: `make spell_check`

## Architecture Overview

This is a LangGraph-based web research agent that uses Google Gemini models and Google Search API to perform multi-step research. The system supports dual deployment modes: LangGraph development server (HTTP + Studio UI) and stdio MCP server for client integration.

### Core Components

- **LangGraph Agent** (`src/agent/graph.py`): State-driven research workflow with nodes for query generation, web research, reflection, and answer synthesis
- **FastMCP HTTP Server** (`src/app.py`): HTTP API that exposes the `deep_search` tool with configurable effort levels
- **FastMCP stdio Server** (`main.py`): stdio transport MCP server that starts LangGraph server and provides MCP integration
- **State Management** (`src/agent/state.py`): TypedDict-based states for different workflow stages

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

- `src/agent/graph.py`: Main LangGraph workflow definition
- `src/app.py`: FastMCP HTTP server with deep_search tool
- `main.py`: FastMCP stdio server with LangGraph server startup and signal handling
- `src/agent/configuration.py`: Agent configuration schema
- `src/agent/prompts.py`: Prompt templates for different workflow stages
- `src/agent/tools_and_schemas.py`: Pydantic schemas for structured outputs
- `tests/test_simple_mcp.py`: tests for stdio MCP server
- `tests/test_stdio_client.py`: Integration test client for MCP stdio protocol