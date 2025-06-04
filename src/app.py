"""ASGI application setup for DeepSearch using FastMCP."""

from fastmcp import FastMCP
from langchain_core.messages import HumanMessage

from agent.graph import graph

mcp = FastMCP("DeepSearch")

# Create the ASGI app
app = mcp.http_app(path="/mcp")

@mcp.tool()
def deep_search(
    query: str,
    initial_search_query_count: int = 3,
    max_research_loops: int = 2,
    query_generator_model: str = "gemini-2.5-flash-preview-05-20",
    reflection_model: str = "gemini-2.5-flash-preview-05-20",
    answer_model: str = "gemini-2.5-pro-preview-05-06"
) -> dict:
    """Perform a deep search on a given query using an advanced web research agent.
    
    Args:
        query: The research question or topic to investigate.
        initial_search_query_count: Number of initial search queries to generate (default: 3).
        max_research_loops: Maximum number of research loops to perform (default: 2).
        query_generator_model: Model for generating search queries (default: gemini-2.5-flash-preview-05-20).
        reflection_model: Model for reflection on search results (default: gemini-2.5-flash-preview-05-20).
        answer_model: Model for generating the final answer (default: gemini-2.5-pro-preview-05-06).
    
    Returns:
        A dictionary containing the answer to the query and a list of sources used.
    """
    # Prepare the input state with the user's query
    input_state = {
        "messages": [HumanMessage(content=query)],
        "search_query": [],
        "web_research_result": [],
        "sources_gathered": [],
        "initial_search_query_count": initial_search_query_count,
        "max_research_loops": max_research_loops,
        "reasoning_model": answer_model
    }
    
    # Configuration for the agent
    config = {
        "configurable": {
            "query_generator_model": query_generator_model,
            "reflection_model": reflection_model,
            "answer_model": answer_model
        }
    }
    
    # Run the agent graph to process the query
    result = graph.invoke(input_state, config)
    
    # Extract the final answer and sources from the result
    answer = result["messages"][-1].content if result["messages"] else "No answer generated."
    sources = result["sources_gathered"]
    
    return {
        "answer": answer,
        "sources": sources
    }