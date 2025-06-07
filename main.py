"""Main entry point for the stdio MCP server."""
import asyncio
import subprocess
import sys
from typing import Annotated, Literal

from fastmcp import FastMCP
from langchain_core.messages import HumanMessage
from pydantic import Field

from src.agent.graph import graph


async def start_langgraph_server():
    """Start the LangGraph server in the background."""
    try:
        # Start LangGraph server as a subprocess
        process = subprocess.Popen(
            ["uv", "run", "langgraph", "dev", "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        await asyncio.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            sys.stderr.write("LangGraph server started successfully\n")
            return process
        else:
            _, stderr = process.communicate()
            sys.stderr.write(f"Failed to start LangGraph server: {stderr}\n")
            return None
    except Exception as e:
        sys.stderr.write(f"Error starting LangGraph server: {e}\n")
        return None


# Create MCP server
mcp = FastMCP("DeepSearch")

@mcp.tool()
async def deep_search(
    query: Annotated[str, Field(description="Search query string")],
    effort: Annotated[
        Literal["low", "medium", "high"], Field(description="Search effort")
    ] = "low",
) -> dict:
    """Perform a deep search on a given query using an advanced web research agent.
    
    Args:
        query: The research question or topic to investigate.
        effort: The amount of effect for the research, low, medium or hight (default: low).
    
    Returns:
        A dictionary containing the answer to the query and a list of sources used.
    """
    # Set search query count, research loops and reasoning model based on effort level
    if effort == "low":
        initial_search_query_count = 1
        max_research_loops = 1
        reasoning_model = "gemini-2.5-flash-preview-05-20"
    elif effort == "medium":
        initial_search_query_count = 3
        max_research_loops = 2
        reasoning_model = "gemini-2.5-flash-preview-05-20"
    else:  # high effort
        initial_search_query_count = 5
        max_research_loops = 3
        reasoning_model = "gemini-2.5-pro-preview-05-06"
    
    # Prepare the input state with the user's query
    input_state = {
        "messages": [HumanMessage(content=query)],
        "search_query": [],
        "web_research_result": [],
        "sources_gathered": [],
        "initial_search_query_count": initial_search_query_count,
        "max_research_loops": max_research_loops,
        "reasoning_model": reasoning_model,
    }

    query_generator_model: str = "gemini-2.5-flash-preview-05-20"
    reflection_model: str = "gemini-2.5-flash-preview-05-20"
    answer_model: str = "gemini-2.5-pro-preview-05-06"
    
    # Configuration for the agent
    config = {
        "configurable": {
            "query_generator_model": query_generator_model,
            "reflection_model": reflection_model,
            "answer_model": answer_model
        }
    }
    
    # Run the agent graph to process the query in a separate thread to avoid blocking
    result = await asyncio.to_thread(graph.invoke, input_state, config)
    
    # Extract the final answer and sources from the result
    answer = result["messages"][-1].content if result["messages"] else "No answer generated."
    sources = result["sources_gathered"]
    
    return {
        "answer": answer,
        "sources": sources
    }


async def setup_and_run():
    """Set up LangGraph server then run MCP server."""
    import atexit
    
    # Start LangGraph server
    langgraph_process = await start_langgraph_server()
    
    def cleanup_langgraph():
        """Cleanup function for atexit."""
        if langgraph_process and langgraph_process.poll() is None:
            langgraph_process.terminate()
            try:
                langgraph_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                langgraph_process.kill()
            sys.stderr.write("LangGraph server stopped\n")
    
    # Register cleanup function
    atexit.register(cleanup_langgraph)
    
    # Note: This function will return and let FastMCP handle the stdio protocol
    sys.stderr.write("Setup complete, MCP server ready\n")


def main():
    """Start LangGraph server and run MCP stdio server."""
    try:
        # Run setup first
        asyncio.run(setup_and_run())
        
        # Add a small delay to ensure everything is ready
        import time
        time.sleep(1)
        
        # Now run MCP server
        sys.stderr.write("Starting MCP stdio server...\n")
        mcp.run(transport="stdio")
        
    except KeyboardInterrupt:
        sys.stderr.write("\nKeyboard interrupt received\n")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    main()