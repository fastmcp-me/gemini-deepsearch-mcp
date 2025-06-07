"""Simple MCP protocol test without external dependencies."""
import asyncio
import json
import os
import subprocess
import sys
from typing import Any, Dict


class SimpleMCPClient:
    """Simple MCP client for testing basic protocol."""
    
    def __init__(self, server_command: list[str]):
        """Initialize the client."""
        self.server_command = server_command
        self.process = None
        self.request_id = 0
    
    async def start(self) -> bool:
        """Start the MCP server and wait for it to be ready."""
        print("Starting MCP server...")
        
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
        
        print("✓ MCP process started")
        
        # Wait for initialization - both LangGraph and MCP servers need time
        print("Waiting for server initialization...")
        for i in range(10):
            await asyncio.sleep(1)
            
            # Check if process is still running
            if self.process.returncode is not None:
                stderr_data = await self.process.stderr.read()
                print(f"✗ MCP server exited: {stderr_data.decode()}")
                return False
            
            print(f"  {i+1}/10 seconds...")
        
        print("✓ Server initialization complete")
        return True
    
    async def send_request(self, method: str, params: Dict[str, Any] = None, timeout: float = 45.0) -> Dict[str, Any]:
        """Send a JSON-RPC request."""
        if not self.process:
            raise RuntimeError("Server not started")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        print(f"→ {method} (timeout: {timeout}s)")
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            print(f"  Sending: {request_json.strip()}")
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            print("  Request sent, waiting for response...")
            
            # Read response with timeout and progress updates
            async def read_with_progress():
                start_time = asyncio.get_event_loop().time()
                while True:
                    try:
                        response_line = await asyncio.wait_for(
                            self.process.stdout.readline(),
                            timeout=5.0  # Check every 5 seconds
                        )
                        return response_line
                    except asyncio.TimeoutError:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed >= timeout:
                            raise asyncio.TimeoutError()
                        print(f"  Still waiting... ({elapsed:.0f}s/{timeout:.0f}s)")
                        continue
            
            response_line = await read_with_progress()
            
            if not response_line:
                # Try to get stderr for debugging
                print("  No response, checking stderr...")
                try:
                    stderr_data = await asyncio.wait_for(self.process.stderr.read(), timeout=2.0)
                    stderr_text = stderr_data.decode().strip()
                    if stderr_text:
                        print(f"  Server stderr: {stderr_text}")
                except asyncio.TimeoutError:
                    print("  No stderr available")
                raise RuntimeError("No response from server")
            
            response_text = response_line.decode().strip()
            print(f"  Raw response: {response_text}")
            response = json.loads(response_text)
            print(f"← Response received successfully")
            return response
            
        except asyncio.TimeoutError:
            print(f"✗ Timeout after {timeout}s")
            # Try to get stderr for debugging
            try:
                stderr_data = await asyncio.wait_for(self.process.stderr.read(), timeout=1.0)
                stderr_text = stderr_data.decode().strip()
                if stderr_text:
                    print(f"  Server stderr during timeout: {stderr_text}")
            except:
                pass
            raise
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {response_line.decode()}")
            raise
    
    async def stop(self):
        """Stop the server."""
        if self.process:
            print("Stopping server...")
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
                print("✓ Server stopped")
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
                print("✓ Server killed")


async def test_mcp():
    """Test basic MCP protocol."""
    print("=== Simple MCP Protocol Test ===\n")
    
    # Setup
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client = SimpleMCPClient(["python", os.path.join(parent_dir, "main.py")])
    
    try:
        # Start server
        if not await client.start():
            return False
        
        print("\n" + "="*40)
        
        # Test 1: Initialize
        print("1. Testing initialize...")
        try:
            response = await client.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            })
            
            if "result" in response:
                print("✓ Initialize successful")
            else:
                print(f"✗ Initialize failed: {response}")
                return False
        except Exception as e:
            print(f"✗ Initialize error: {e}")
            return False
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        try:
            response = await client.send_request("tools/list")
            
            if "result" in response:
                tools = response["result"].get("tools", [])
                print(f"✓ Found {len(tools)} tools")
                for tool in tools:
                    print(f"  - {tool.get('name')}")
            else:
                print(f"✗ Tools list failed: {response}")
                return False
        except Exception as e:
            print(f"✗ Tools list error: {e}")
            return False
        
        print("\n✅ MCP protocol working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        await client.stop()


if __name__ == "__main__":
    try:
        success = asyncio.run(test_mcp())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)