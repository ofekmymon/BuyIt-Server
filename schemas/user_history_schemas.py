from pydantic import BaseModel


class UserVisitedSchema(BaseModel):
    user_id: str
    item_id: str


class UserSearchHistory(BaseModel):
    user_id: str
    search_query: str


__all__ = ["UserVisitedSchema", "UserSearchHistory"]
