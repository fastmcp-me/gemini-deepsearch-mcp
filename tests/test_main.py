"""Tests for the stdio MCP server."""
import asyncio
import json
import subprocess
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import deep_search, mcp, start_langgraph_server


class TestLangGraphServerStartup:
    """Test LangGraph server startup functionality."""

    @patch("main.subprocess.Popen")
    @patch("main.asyncio.sleep")
    async def test_start_langgraph_server_success(self, mock_sleep, mock_popen):
        """Test successful LangGraph server startup."""
        # Mock process that starts successfully
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        result = await start_langgraph_server()
        
        assert result == mock_process
        mock_popen.assert_called_once_with(
            ["uv", "run", "langgraph", "dev", "--host", "127.0.0.1", "--port", "8123"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        mock_sleep.assert_called_once_with(3)

    @patch("main.subprocess.Popen")
    @patch("main.asyncio.sleep")
    async def test_start_langgraph_server_failure(self, mock_sleep, mock_popen):
        """Test LangGraph server startup failure."""
        # Mock process that fails to start
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = ("", "Server failed to start")
        mock_popen.return_value = mock_process
        
        result = await start_langgraph_server()
        
        assert result is None
        mock_process.communicate.assert_called_once()

    @patch("main.subprocess.Popen")
    async def test_start_langgraph_server_exception(self, mock_popen):
        """Test LangGraph server startup with exception."""
        mock_popen.side_effect = Exception("Command not found")
        
        result = await start_langgraph_server()
        
        assert result is None


class TestDeepSearchTool:
    """Test the deep_search MCP tool."""

    @patch("main.graph.invoke")
    @patch("main.asyncio.to_thread")
    async def test_deep_search_low_effort(self, mock_to_thread, mock_graph_invoke):
        """Test deep_search with low effort level."""
        # Mock graph response
        mock_result = {
            "messages": [MagicMock(content="Test answer")],
            "sources_gathered": ["source1.com", "source2.com"]
        }
        mock_to_thread.return_value = mock_result
        mock_graph_invoke.return_value = mock_result
        
        result = await deep_search("What is AI?", "low")
        
        assert result["answer"] == "Test answer"
        assert result["sources"] == ["source1.com", "source2.com"]
        
        # Verify the configuration for low effort
        call_args = mock_to_thread.call_args
        input_state = call_args[0][1]  # Second argument to graph.invoke
        assert input_state["initial_search_query_count"] == 1
        assert input_state["max_research_loops"] == 1
        assert input_state["reasoning_model"] == "gemini-2.5-flash-preview-05-20"

    @patch("main.graph.invoke")
    @patch("main.asyncio.to_thread")
    async def test_deep_search_medium_effort(self, mock_to_thread, mock_graph_invoke):
        """Test deep_search with medium effort level."""
        mock_result = {
            "messages": [MagicMock(content="Test answer")],
            "sources_gathered": ["source1.com"]
        }
        mock_to_thread.return_value = mock_result
        
        result = await deep_search("What is machine learning?", "medium")
        
        # Verify the configuration for medium effort
        call_args = mock_to_thread.call_args
        input_state = call_args[0][1]
        assert input_state["initial_search_query_count"] == 3
        assert input_state["max_research_loops"] == 2
        assert input_state["reasoning_model"] == "gemini-2.5-flash-preview-05-20"

    @patch("main.graph.invoke")
    @patch("main.asyncio.to_thread")
    async def test_deep_search_high_effort(self, mock_to_thread, mock_graph_invoke):
        """Test deep_search with high effort level."""
        mock_result = {
            "messages": [MagicMock(content="Test answer")],
            "sources_gathered": []
        }
        mock_to_thread.return_value = mock_result
        
        result = await deep_search("Complex research question", "high")
        
        # Verify the configuration for high effort
        call_args = mock_to_thread.call_args
        input_state = call_args[0][1]
        assert input_state["initial_search_query_count"] == 5
        assert input_state["max_research_loops"] == 3
        assert input_state["reasoning_model"] == "gemini-2.5-pro-preview-05-06"

    @patch("main.graph.invoke")
    @patch("main.asyncio.to_thread")
    async def test_deep_search_no_messages(self, mock_to_thread, mock_graph_invoke):
        """Test deep_search when no messages are returned."""
        mock_result = {
            "messages": [],
            "sources_gathered": []
        }
        mock_to_thread.return_value = mock_result
        
        result = await deep_search("Test query", "low")
        
        assert result["answer"] == "No answer generated."
        assert result["sources"] == []


class TestStdioMCPServer:
    """Test stdio MCP server functionality."""

    def test_mcp_server_creation(self):
        """Test that MCP server is created correctly."""
        assert mcp.name == "DeepSearch"
        assert hasattr(mcp, "tools")
        assert "deep_search" in [tool.name for tool in mcp.tools]

    async def test_mcp_tool_registration(self):
        """Test that deep_search tool is properly registered."""
        tool_names = [tool.name for tool in mcp.tools]
        assert "deep_search" in tool_names
        
        # Find the deep_search tool
        deep_search_tool = next(tool for tool in mcp.tools if tool.name == "deep_search")
        assert deep_search_tool.description is not None
        assert "research" in deep_search_tool.description.lower()


class TestStdioMCPIntegration:
    """Integration tests for stdio MCP server."""

    @pytest.mark.asyncio
    async def test_stdio_mcp_protocol(self):
        """Test basic MCP protocol over stdio."""
        # This test would require actually running the MCP server process
        # and communicating with it over stdio, which is complex for unit tests
        # Instead, we'll test the tool directly
        
        with patch("main.graph.invoke") as mock_graph:
            mock_graph.return_value = {
                "messages": [MagicMock(content="Test response")],
                "sources_gathered": ["test.com"]
            }
            
            # Test the tool function directly
            result = await deep_search("test query", "low")
            assert "answer" in result
            assert "sources" in result

    def test_mcp_tool_schema(self):
        """Test that MCP tool has correct schema."""
        # Find the deep_search tool
        deep_search_tool = next(tool for tool in mcp.tools if tool.name == "deep_search")
        
        # Check that it has the expected parameters
        assert hasattr(deep_search_tool, 'inputSchema')
        
        # The schema should include query and effort parameters
        schema = deep_search_tool.inputSchema
        assert "properties" in schema
        properties = schema["properties"]
        assert "query" in properties
        assert "effort" in properties
        
        # Check effort enum values
        effort_schema = properties["effort"]
        assert "enum" in effort_schema or "anyOf" in effort_schema


@pytest.mark.integration
class TestFullStdioMCPServer:
    """Full integration tests that actually start the server process."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Test that the server can start and shutdown gracefully."""
        # This would be a more complex integration test
        # that actually starts the main.py process and tests stdio communication
        pytest.skip("Integration test requires actual server startup")

    @pytest.mark.asyncio  
    async def test_mcp_stdio_communication(self):
        """Test actual MCP communication over stdio."""
        # This would test the full MCP protocol
        pytest.skip("Integration test requires MCP client implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])