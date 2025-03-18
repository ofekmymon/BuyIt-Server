from pydantic import BaseModel


class QueryBySearchSchema(BaseModel):
    search: str
    products_number: int


__all__ = ["QueryBySearchSchema"]
