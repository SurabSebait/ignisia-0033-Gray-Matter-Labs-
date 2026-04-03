# AI-Powered Customer Support Platform

A production-grade customer support platform with AI-assisted responses, multi-role access, and Streamlit frontend.

## Features

- **Unified Login Portal**: Single entry point with automatic role-based redirection
- **Role-Based Access Control**: Secure JWT authentication with middleware protection
- **Zendesk-Inspired UI**: Modern, responsive design with gradient headers and card-based layouts
- **User Portal**: Create tickets and chat with support
- **Admin Portal**: Upload documents (PDF, Excel, Email) to update knowledge base
- **Support Personnel Portal**: 3-panel interface for managing tickets, chatting, and viewing citations
- **Ticket Locking**: Prevent concurrent access to tickets
- **File Ingestion Tracking**: Monitor document processing status
- **Similar Tickets**: AI-powered suggestions for support agents
- **Search & Filters**: Advanced ticket filtering in support portal
- **Authentication**: Role-based login system (user/admin/support)
- **Ticket Locking**: Prevent concurrent access to tickets
- **File Ingestion Tracking**: Monitor document processing status
- **Similar Tickets**: AI-powered suggestions for support agents
- **Search & Filters**: Advanced ticket filtering in support portal

## Architecture

The platform uses a **unified Streamlit frontend** and a **FastAPI backend** with JWT authentication and MongoDB.

### Frontend Structure

- `main.py`: Unified app with conditional rendering based on user role

### Backend Structure

- **Routers**: Modular API endpoints with role-based access control
- **Services**: Business logic layer
- **Models**: Pydantic data models
- **Database**: MongoDB with optimized indexes

### Security

- JWT-based authentication with role validation
- Role-based access control (User, Admin, Support)
- Users can only access their own tickets
- Support/Admin have restricted permissions

- **Backend**: FastAPI with async MongoDB (Motor), JWT authentication middleware
- **Frontend**: Single Streamlit app with role-based routing and Zendesk-inspired UI
- **Database**: MongoDB with optimized indexes
- **Authentication**: JWT tokens with role-based access control

## Setup

### 1) Create Python virtual environments

```powershell
cd C:\Ignisia
python -m venv .venv-backend
.\.venv-backend\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# in separate shell for frontend
python -m venv .venv-frontend
.\.venv-frontend\Scripts\Activate.ps1
pip install -r frontend/requirements.txt
```

### 2) Create `.env` (root of repository)

File: `C:\Ignisia\.env`

```text
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=customer_support
GCS_BUCKET_NAME=your-bucket-name
OPENAI_API_KEY=your-openai-api-key
AI_MODEL=gpt-4.1
AI_SERVICE_URL=
ENABLE_AI_RESPONSE=true
ENABLE_VECTOR_UPDATE=true
```

### 3) Start MongoDB

Ensure MongoDB is running locally on port 27017.

### 4) Create initial users

Start the backend first, then create users using PowerShell:

```powershell
# Register users via API
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/auth/register" -ContentType "application/json" -Body '{"username":"user1","password":"pass","role":"user"}'
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/auth/register" -ContentType "application/json" -Body '{"username":"admin1","password":"pass","role":"admin"}'
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/auth/register" -ContentType "application/json" -Body '{"username":"support1","password":"pass","role":"support"}'
```

### 5) Run backend

```powershell
cd C:\Ignisia
.\.venv-backend\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 6) Run frontend

```powershell
cd C:\Ignisia
.\.venv-frontend\Scripts\Activate.ps1
streamlit run frontend/main.py
```

The frontend will open at `http://localhost:8501` with the unified login and dashboard interface.

### 7) Validation

- `GET http://localhost:8000/` should return API health object
- `GET http://localhost:8000/tickets/` should return empty list after startup
- `POST http://localhost:8000/ai/generate-response` should return `response` + `citations`

---

## Authentication

- **Users**: Login with username/password to access user portal
- **Admins**: Login to upload files and manage knowledge base
- **Support**: Login to view 3-panel ticket management interface

Use the register endpoint to create users or hardcode in database for demo.

---

## ENV usage in backend

- `backend/app/config/settings.py` reads `.env` automatically via `BaseSettings`
- `backend/app/routers/ai.py` now imports `settings` and uses `openai_api_key`, `ai_model`
- `backend/app/routers/vector.py` now uses `settings.gcs_bucket_name` and stores file metadata in `files`

## API Endpoints

- `POST /auth/register` - Register user
- `POST /auth/login` - Login user
- `POST /tickets/` - Create ticket
- `GET /tickets/` - List tickets
- `GET /tickets/{id}` - Get ticket
- `PATCH /tickets/{id}` - Update ticket
- `PATCH /tickets/{id}/lock` - Lock ticket
- `PATCH /tickets/{id}/unlock` - Unlock ticket
- `GET /tickets/{id}/similar` - Get similar tickets
- `POST /messages/{ticket_id}/messages` - Create message
- `GET /messages/{ticket_id}/messages` - Get messages
- `POST /ai/generate-response` - Generate AI response with citations
- `POST /vector/update` - Update vector store (stub)
- `POST /files/` - Create file record
- `PATCH /files/{id}/status` - Update file status

## Database Schemas

See `backend/app/models/` for Pydantic models.

## Example Payloads

### Create Ticket

```json
{
  "user_id": "user123",
  "query": "How to reset password?"
}
```

### AI Response Request

```json
{
  "ticket_id": "60d5ecb74b24c72b8c8b4567",
  "query": "How to reset password?",
  "conversation_history": ["How to reset password?"]
}
```

### AI Response

```json
{
  "id": "60d5ecb74b24c72b8c8b4568",
  "ticket_id": "60d5ecb74b24c72b8c8b4567",
  "response": "To reset your password, go to settings...",
  "citations": [
    {
      "text": "Password reset instructions...",
      "source_type": "pdf",
      "source_name": "user_manual.pdf",
      "reference": "page 10",
      "relevance_score": 0.95
    }
  ]
}
```
