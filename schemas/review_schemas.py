from pydantic import BaseModel


class ReviewSchema(BaseModel):
    username: str
    user_id: str
    product_id: str
    review_text: str
    rating: int


__all__ = ["ReviewSchema"]
