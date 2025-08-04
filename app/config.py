import os
from dotenv import load_dotenv

load_dotenv()

REMOTE_URL = os.getenv("REMOTE_MCP_URL", "http://0.0.0.0:8001/sse")
MCP_TOKEN = os.getenv("REMOTE_MCP_AUTH_TOKEN", None)
