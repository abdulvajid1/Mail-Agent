from fastmcp import Client
from fastmcp.exceptions import FastMCPError
import asyncio
from job_agent.config import MCP_SERVER_PATH

from langchain_mcp_adapters.client import MultiServerMCPClient 



def connect_to_mcp():
    client = MultiServerMCPClient({
            "gmail": {
                "transport": "stdio",  # Local subprocess communication
                "command": "python",
                # Absolute path to your math_server.py file
                "args": ["src/job_agent/mcp/server.py"],
            }
        }) # type: ignore
    
    return client


# def connect_to_mcp(stdio_server_path="src\job_agent\mcp\server.py"):
#     try:
#         client = Client(stdio_server_path)
#         return client
#     except FastMCPError as e:
#         raise Exception(f"Error in Connecting to MCP : {e}")

# async def main():
#     async with client:
#         # Basic server interaction
#         await client.ping()

#         # List available operations
#         tools = await client.list_tools()
#         resources = await client.list_resources()
#         prompts = await client.list_prompts()

#         # Execute operations
#         result = await client.call_tool("example_tool", {"param": "value"})
#         print(result)

# asyncio.run(main())