"""All system configs"""
from pathlib import Path

MCP_SERVER_PATH = Path("src", "job_agent", "mcp", "server.py")
CONFIG_PATH = Path.home() / ".agent" / "config.json"
CREDENTIALS = {"installed":{"client_id":"553445846532-s3gkvdjb18gjebbjcb32ccnllfob2vck.apps.googleusercontent.com","project_id":"job-mail-agent-502002","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}