from pydantic import BaseModel


class StarboardMessage(BaseModel):
    channel_id: int
    message: str
