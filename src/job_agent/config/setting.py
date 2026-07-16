"""All configs"""
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()
MODEL_NAME = os.environ['MODEL_NAME']
MCP_SERVER_PATH = Path("src", "job_agent", "mcp", "server.py")
CONFIG_PATH = Path.home() / ".agent" / "config.json"
