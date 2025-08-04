from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()

def ensure_session_exists(user_id: str, session_id: str = "sess1"):
    if not session_service.get_session("Monitor_agent_app", user_id, session_id):
        session_service.create_session("Monitor_agent_app", user_id, session_id)
