from pydantic import BaseModel
from datetime import datetime


class CommentData(BaseModel):
    id: str
    idx: int
    user_url: str
    user_id: str
    user_name: str
    post_time: datetime | None
    content: str
    quotes: list["QuoteData"] | None
    json_content: str


class QuoteData(BaseModel):
    parent_comment_id: str
    content: str
