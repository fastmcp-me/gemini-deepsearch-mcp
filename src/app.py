from fastmcp import FastMCP

mcp = FastMCP("DeepSearch")

# Create the ASGI app
app = mcp.http_app(path="/mcp")
