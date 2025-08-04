from fastapi import APIRouter
from fastapi.responses import JSONResponse
from google.genai import types

from .schemas import ChatRequest
from .agent import runner
from .session import ensure_session_exists

router = APIRouter()

@router.post("/chat")
async def chat(req: ChatRequest):
    ensure_session_exists(req.user_id)

    prompt = types.Content(role="user", parts=[types.Part(text=req.message)])
    full_response = ""

    try:
        async for evt in runner.run_async(user_id=req.user_id, session_id="sess1", new_message=prompt):
            if evt.is_final_response():
                for part in evt.content.parts:
                    full_response += part.text
        return JSONResponse(content={"response": full_response})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
