from fastapi import FastAPI
from app.routers import tickets, messages, ai, vector, auth, files
from app.db.connection import connect_to_mongo, close_mongo_connection
from app.config.settings import settings

app = FastAPI(title="AI Customer Support Platform", version="1.0.0")

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(vector.router, prefix="/vector", tags=["vector"])
app.include_router(files.router, prefix="/files", tags=["files"])

@app.get("/")
async def root():
    return {"message": "AI Customer Support Platform API"}