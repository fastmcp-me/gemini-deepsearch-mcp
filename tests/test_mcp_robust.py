"""Robust test for MCP stdio server with better debugging."""
import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict


async def check_langgraph_server(port: int = 2024, timeout: float = 30.0) -> bool:
    """Check if LangGraph server is responding on the given port."""
    try:
        import aiohttp
    except ImportError:
        print(f"⚠️  aiohttp not available, skipping LangGraph server check on port {port}")
        return True  # Assume it's working if we can't check
    
    url = f"http://127.0.0.1:{port}/ok"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2.0) as response:
                    if response.status == 200:
                        print(f"✓ LangGraph server responding on port {port}")
                        return True
        except Exception:
            pass
        
        await asyncio.sleep(1)
    
    print(f"✗ LangGraph server not responding on port {port} after {timeout}s")
    return False


class RobustMCPClient:
    """MCP client with better error handling and debugging."""
    
    def __init__(self, server_command: list[str]):
        """Initialize the client."""
        self.server_command = server_command
        self.process = None
        self.request_id = 0
    
    async def start(self) -> bool:
        """Start the MCP server and wait for it to be ready."""
        print("Starting MCP server process...")
        
        # Get parent directory for running main.py
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=parent_dir
        )
        
        print("✓ MCP process started, waiting for initialization...")
        
        # Wait longer for initialization and check periodically
        for i in range(15):  # 15 seconds total
            await asyncio.sleep(1)
            
            # Check if process is still running
            if self.process.returncode is not None:
                stderr_data = await self.process.stderr.read()
                print(f"✗ MCP server exited early: {stderr_data.decode()}")
                return False
            
            print(f"  Waiting... ({i+1}/15)")
        
        # Check if LangGraph server is responding
        print("\nChecking LangGraph server...")
        langgraph_ok = await check_langgraph_server()
        
        if not langgraph_ok:
            print("⚠️  LangGraph server not responding, but continuing with MCP test...")
        
        print("✓ MCP server should be ready for requests")
        return True
    
    async def send_request(self, method: str, params: Dict[str, Any] = None, timeout: float = 15.0) -> Dict[str, Any]:
        """Send a JSON-RPC request with better error handling."""
        if not self.process:
            raise RuntimeError("Server not started")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        print(f"→ Sending {method} request...")
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            print(f"  Request sent: {request_json.strip()}")
            
            # Read response with timeout
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=timeout
            )
            
            if not response_line:
                # Try to get stderr
                try:
                    stderr_data = await asyncio.wait_for(self.process.stderr.read(), timeout=2.0)
                    stderr_text = stderr_data.decode()
                    if stderr_text.strip():
                        print(f"  Server stderr: {stderr_text}")
                except asyncio.TimeoutError:
                    pass
                raise RuntimeError("No response from server")
            
            response_text = response_line.decode().strip()
            print(f"← Received response: {response_text}")
            
            response = json.loads(response_text)
            return response
            
        except asyncio.TimeoutError:
            print(f"✗ Request timeout after {timeout}s")
            raise
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON response: {response_line.decode()}")
            raise
    
    async def stop(self):
        """Stop the server process."""
        if self.process:
            print("Stopping MCP server...")
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
                print("✓ Server stopped cleanly")
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
                print("✓ Server killed")


async def test_mcp_protocol():
    """Test the MCP protocol with robust error handling."""
    print("=== Robust MCP Protocol Test ===\n")
    
    # Setup client
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client = RobustMCPClient(["python", os.path.join(parent_dir, "main.py")])
    
    try:
        # Start server with better monitoring
        if not await client.start():
            print("❌ Failed to start MCP server")
            return False
        
        print("\n" + "="*50)
        print("Testing MCP Protocol Communication")
        print("="*50)
        
        # Test 1: Initialize
        try:
            print("\n1. Testing MCP initialize...")
            init_response = await client.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            })
            
            if "result" in init_response:
                print("✓ Initialize successful")
                print(f"  Server capabilities: {init_response['result'].get('capabilities', {})}")
            else:
                print(f"✗ Initialize failed: {init_response}")
                return False
                
        except Exception as e:
            print(f"✗ Initialize failed: {e}")
            return False
        
        # Test 2: List tools
        try:
            print("\n2. Testing tools/list...")
            tools_response = await client.send_request("tools/list")
            
            if "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                print(f"✓ Found {len(tools)} tools")
                for tool in tools:
                    print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
            else:
                print(f"✗ Tools list failed: {tools_response}")
                return False
                
        except Exception as e:
            print(f"✗ Tools list failed: {e}")
            return False
        
        print("\n✅ Basic MCP protocol working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        await client.stop()


if __name__ == "__main__":
    try:
        success = asyncio.run(test_mcp_protocol())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        sys.exit(1)