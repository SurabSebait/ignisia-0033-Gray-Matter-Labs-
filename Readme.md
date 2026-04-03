
# AI-Powered Customer Support Platform

A production-grade customer support platform with AI-assisted responses, multi-role access, and Streamlit frontend.

## Features

- **User Portal**: Create tickets and chat with support
- **Admin Portal**: Upload documents (PDF, Excel, Email) to update knowledge base
- **Support Personnel Portal**: 3-panel interface for managing tickets, chatting, and viewing citations

## Architecture

- **Backend**: FastAPI with async MongoDB (Motor)
- **Frontend**: Streamlit for all UIs
- **Database**: MongoDB
- **AI Integration**: External RAG pipeline (not implemented here)

## Setup

### Backend

1. Install dependencies: `pip install -r backend/requirements.txt`
2. Set environment variables in `.env` (MongoDB URL, GCS credentials)
3. Run: `uvicorn backend.main:app --reload`

### Frontend

1. Install dependencies: `pip install -r frontend/requirements.txt`
2. Run user UI: `streamlit run frontend/user_ui.py`
3. Run admin UI: `streamlit run frontend/admin_ui.py`
4. Run support UI: `streamlit run frontend/support_ui.py`

## API Endpoints

- `POST /tickets/` - Create ticket
- `GET /tickets/` - List tickets
- `GET /tickets/{id}` - Get ticket
- `PATCH /tickets/{id}` - Update ticket
- `POST /messages/{ticket_id}/messages` - Create message
- `GET /messages/{ticket_id}/messages` - Get messages
- `POST /ai/generate-response` - Generate AI response with citations
- `POST /vector/update` - Update vector store (stub)

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
