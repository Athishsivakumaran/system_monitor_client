from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from .session import session_service
from .config import REMOTE_URL, MCP_TOKEN

agent = None
runner = None
exit_stack = None

async def init_agent():
    global agent, runner, exit_stack

    session_params = SseServerParams(
        url=REMOTE_URL,
        headers={"Authorization": f"Bearer {MCP_TOKEN}"} if MCP_TOKEN else None
    )

    tools, exit_stack = await MCPToolset.from_server(connection_params=session_params)

    agent = LlmAgent(
        name="System_Monitor_Agent",
        model="gemini-1.5-flash",
        instruction=(
            "You are a system monitoring assistant. "
            "Use available tools to check memory or CPU usage, compare current and past usage, "
            "alert on high memory, or summarize system performance. Be concise and accurate. "
            "You have access to external tools via MCP. Use them when needed."
        ),
        tools=tools
    )

    session_service.create_session("Monitor_agent_app", user_id="user1", session_id="sess1")
    runner = Runner(agent=agent, app_name="Monitor_agent_app", session_service=session_service)

async def shutdown_agent():
    global exit_stack
    if exit_stack:
        await exit_stack.aclose()
