import os
import boto3
from fastapi import File, UploadFile
from pydantic import BaseModel
from typing import List, Optional

# AWS S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


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
