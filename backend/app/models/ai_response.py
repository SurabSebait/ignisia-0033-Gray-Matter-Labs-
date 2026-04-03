from pydantic import BaseModel
from typing import List, Optional

class Citation(BaseModel):
    text: str
    source_type: str  # pdf/excel/email
    source_name: str
    reference: str  # page/row/thread
    relevance_score: Optional[float]

class AIResponseRequest(BaseModel):
    ticket_id: str
    query: str
    conversation_history: List[str]

class AIResponse(BaseModel):
    id: str
    ticket_id: str
    message_id: Optional[str]
    response: str
    citations: List[Citation]

    class Config:
        orm_mode = True