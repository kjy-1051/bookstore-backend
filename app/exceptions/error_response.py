from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union

class ErrorResponse(BaseModel):
    timestamp: str
    path: str
    status: int
    code: str
    message: str
    details: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
