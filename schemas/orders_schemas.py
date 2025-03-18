from pydantic import BaseModel


class OrderSchema(BaseModel):
    user_id: str
    product_id: str
    address: str
    quantity: int


class DeleteOrderSchema(BaseModel):
    user_id: str
    order_id: str
    product_id: str
    quantity: int
    order_date: str


__all__ = ["OrderSchema", "DeleteOrderSchema"]
