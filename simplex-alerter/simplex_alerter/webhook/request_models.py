from pydantic import BaseModel

class Alert(BaseModel):
    title: str
    message: str
