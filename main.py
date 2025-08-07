import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# OpenAI Agents imports (with MCP extension)
from agents import Agent, Runner 
from agents.extensions.models.litellm_model import LitellmModel
from agents.mcp import MCPServerSse
from agents.run_context import RunContext

# == Load env ==
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
REMOTE_URL = os.getenv("REMOTE_MCP_URL", "http://0.0.0.0:8001/sse")
MCP_TOKEN = os.getenv("REMOTE_MCP_AUTH_TOKEN")

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

agent: Agent
exit_stack = None

@app.on_event("startup")
async def init_agent():
    global agent, exit_stack

    # 1) Start MCP SSE server connection
    system_monitor_mcp =  MCPServerSse.create(
        name="SystemMonitorMCP",
        params={
            "url": REMOTE_URL,
            "headers": {"Authorization": f"Bearer {MCP_TOKEN}"} if MCP_TOKEN else {},
        },
        cache_tools_list=True,
    )

    # 2) Build LitellmModel wrapper (LiteLLM provider)
    model = LitellmModel(
        model="gemini-2.5-flash",
        api_key=GOOGLE_API_KEY,
    )

    # 3) Create agent with instructions and the MCP tools
    agent = Agent(
        name="SystemMonitorAgent",
        instructions=(
            "You are a concise, accurate system monitoring assistant: "
            "use available tools  to check CPU/memory usage, alert "
            "on high memory, and summarize performance."
        ),
        model=model,
        mcp_servers=[system_monitor_mcp]
    )


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        ctx = RunContext()
        result = await Runner.run(agent, req.message, context=ctx)
        return JSONResponse(content={"response": result.final_output})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
