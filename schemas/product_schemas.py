from fastapi import File, UploadFile
from pydantic import BaseModel
from typing import List, Optional


class ProductSchema(BaseModel):
    seller: str
    name: str
    images: List[UploadFile] = File(...)
    category: str
    tags: List[str]
    details: str
    price: float
    ratings: Optional[List[int]] = []


class ProductsFromTagsSchema(BaseModel):
    tags: List[str]


__all__ = ["ProductSchema", "ProductsFromTagsSchema"]
