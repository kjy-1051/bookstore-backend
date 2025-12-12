from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RatingCreate(BaseModel):
    score: int


class RatingResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    score: int
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
