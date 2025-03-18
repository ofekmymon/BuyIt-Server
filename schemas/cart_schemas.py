from pydantic import BaseModel
from typing import List


class CartItem(BaseModel):
    product_id: str
    quantity: int


class SaveLocalCart(BaseModel):
    local_cart: List[CartItem]
    email: str


class MutateCartSchema(BaseModel):
    email: str
    product: CartItem


__all__ = ["CartItem", "SaveLocalCart", "MutateCartSchema"]
