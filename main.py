import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# OpenAI Agents imports (with MCP extension)
from agents import Agent, Runner 
from agents.extensions.models.litellm_model import LitellmModel
from agents.mcp import MCPServerSse


# == Load env ==
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
REMOTE_URL = os.getenv("REMOTE_MCP_URL")
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
    system_monitor_mcp = MCPServerSse(
        name="SystemMonitorMCP",
        params={
            "url": REMOTE_URL,
            "headers": {"Authorization": f"Bearer {MCP_TOKEN}"} if MCP_TOKEN else {},
        },
        cache_tools_list=True,
    )
    
    # Connect to the MCP server with error handling
    try:
        await system_monitor_mcp.connect()
        print(f"✅ Successfully connected to MCP server at {REMOTE_URL}")
    except Exception as e:
        print(f"❌ Failed to connect to MCP server at {REMOTE_URL}: {e}")
        print("⚠️  Starting agent without MCP tools - some functionality may be limited")
        # Continue without MCP servers
        system_monitor_mcp = None

    # 2) Build LitellmModel wrapper (LiteLLM provider)
    model = LitellmModel(
        model="gemini-2.5-flash",
        api_key=GOOGLE_API_KEY,
    )

    # 3) Create agent with instructions and the MCP tools
    mcp_servers = [system_monitor_mcp] if system_monitor_mcp else []
    agent = Agent(
    name="SystemMonitorAgent",
    instructions=(
        "You are a concise and accurate system monitoring assistant. "
        "You provide clear, human-readable summaries of current system performance "
        "in one or two sentences, covering memory and CPU usage where relevant. "
        "You can also confirm if a high-memory alert has been triggered or if the threshold has been updated. "
        "When reporting on memory usage, mention whether an alert has been sent or is active. "
        "Use plain language and optionally bold key numbers for emphasis. "
        "Never display raw tool output, tool names, or intermediate steps. "
        "If data is missing, say so briefly. "
        "Example: 'Memory usage is at 92%, exceeding the set threshold; a high-memory alert has been sent. "
        "CPU usage is moderate at 43%.' "
        "Do not use markdown  and be conversational."
    ),
    model=model,
    mcp_servers=mcp_servers
)



@app.on_event("shutdown")
async def cleanup():
    global agent, exit_stack
    if agent and hasattr(agent, 'mcp_servers'):
        for server in agent.mcp_servers:
            if server is not None:
                try:
                    await server.cleanup()
                except Exception as e:
                    print(f"Error cleaning up MCP server {server.name}: {e}")
    if exit_stack:
        await exit_stack.aclose()


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = await Runner.run(agent, req.message, context=None)
        print("result", result)
        return JSONResponse(content={"response": result.final_output})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
