from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CommentCreate(BaseModel):
    book_id: int
    content: str

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
