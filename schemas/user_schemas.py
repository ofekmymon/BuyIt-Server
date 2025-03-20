from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from schemas.cart_schemas import CartItem


class UserSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=12)
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=12)
    verified: bool = False
    address: Optional[str] = None
    cart: Optional[List[CartItem]] = []


class GetUserDataSchema(BaseModel):
    id: str


class SignInSchema(BaseModel):
    email: str
    password: str
    remember: bool


class EmailSchema(BaseModel):
    email: str


class EditDetailsSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=12)
    address: Optional[str] = None
    userValidationEmail: str


class VerificationCodeSchema(BaseModel):
    code: str
    email: str


__all__ = ["UserSchema", "GetUserDataSchema", "VerificationCodeSchema",
           "SignInSchema", "EmailSchema", "EditDetailsSchema"]
