from pydantic import BaseModel


class WelcomeMessage(BaseModel):
    channel_id: int
    message: str
