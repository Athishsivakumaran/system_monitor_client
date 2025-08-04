from fastapi import FastAPI
from app.routes import router
from app.agent import init_agent, shutdown_agent

app = FastAPI(title="System Monitor Agent")

@app.on_event("startup")
async def startup_event():
    await init_agent()

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_agent()

app.include_router(router)
