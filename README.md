# Gemini DeepSearch MCP

Gemini DeepSearch MCP is an automated research agent that leverages Google Gemini models and Google Search to perform deep, multi-step web research. It generates sophisticated queries, synthesizes information from search results, identifies knowledge gaps, and produces high-quality, citation-rich answers.

## Features

- **Automated multi-step research** using Gemini models and Google Search
- **FastMCP integration** for both HTTP API and stdio deployment
- **Configurable effort levels** (low, medium, high) for research depth
- **Citation-rich responses** with source tracking
- **LangGraph-powered workflow** with state management

## Usage

### Development Server (HTTP + Studio UI)
Start the LangGraph development server with Studio UI:
```bash
make dev
```

### Local MCP Server (stdio)
Start the MCP server with stdio transport for integration with MCP clients:
```bash
make local
```

### Testing
Run the test suite:
```bash
make test
```

Test the MCP stdio server:
```bash
make test_mcp
```

## API

The `deep_search` tool accepts:
- **query** (string): The research question or topic to investigate
- **effort** (string): Research effort level - "low", "medium", or "high"
  - **Low**: 1 query, 1 loop, Flash model
  - **Medium**: 3 queries, 2 loops, Flash model  
  - **High**: 5 queries, 3 loops, Pro model

Returns:
- **answer**: Comprehensive research response with citations
- **sources**: List of source URLs used in research

## Requirements

- Python 3.12+
- `GEMINI_API_KEY` environment variable

## Claude Desktop Integration

To use the MCP server with Claude Desktop, add this configuration to your Claude Desktop config file:

### macOS
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-deepsearch": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/path/to/gemini-deepsearch-mcp",
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

### Windows
Edit `%APPDATA%/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-deepsearch": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "C:\\path\\to\\gemini-deepsearch-mcp",
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

### Linux
Edit `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-deepsearch": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/path/to/gemini-deepsearch-mcp",
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

**Important:** 
- Replace `/path/to/gemini-deepsearch-mcp` with the actual absolute path to your project directory
- Replace `your-gemini-api-key-here` with your actual Gemini API key
- Restart Claude Desktop after updating the configuration

Once configured, you can use the `deep_search` tool in Claude Desktop by asking questions like:
- "Use deep_search to research the latest developments in quantum computing"
- "Search for information about renewable energy trends with high effort"

## Agent Source
The deep search agent is from the [Gemini Fullstack LangGraph Quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart) repository.


## License
MIT