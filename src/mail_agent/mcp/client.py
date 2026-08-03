import sys
from langchain_mcp_adapters.client import MultiServerMCPClient


def connect_to_mcp():
    client = MultiServerMCPClient({
        "gmail": {
            "transport": "stdio",
            "command": sys.executable,   # the exact interpreter currently running this code
            "args": ["-m", "mail_agent.mcp.server"],
        }
    })
    return client