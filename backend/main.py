from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tickets, messages, ai, vector, auth, files
from app.db.connection import connect_to_mongo, close_mongo_connection
from app.config.settings import settings
from jose import jwt
from datetime import datetime

app = FastAPI(title="AI Customer Support Platform", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Authentication middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for login/register endpoints
    if request.url.path in ["/auth/login", "/auth/register", "/docs", "/openapi.json", "/"]:
        response = await call_next(request)
        return response
    
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Add user info to request state
        request.state.user = username
        request.state.role = role
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    response = await call_next(request)
    return response

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(vector.router, prefix="/vector", tags=["vector"])
app.include_router(files.router, prefix="/files", tags=["files"])

@app.get("/")
async def root():
    return {"message": "AI Customer Support Platform API"}