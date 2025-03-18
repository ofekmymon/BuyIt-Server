import json
from typing import List
from fastapi import APIRouter, File, Form, UploadFile
from services.products_service import upload_product_db, images_to_links
from services.users_service import check_if_user_valid
from schemas.product_schemas import ProductSchema


router = APIRouter(prefix="/auth")


@router.post("/upload-product")
# uploads product to db and images to aws cloud
async def upload_product(
    seller: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    details: str = Form(...),
    tags: str = Form(...),
    price: float = Form(...),
    images: List[UploadFile] = File(...),
):
    tag_values = json.loads(tags)
    product = ProductSchema(
        seller=seller,
        name=name,
        category=category,
        details=details,
        tags=tag_values,
        price=price,
        images=images,
    )
    # holds the urls to be saved in the db with the product
    if (await check_if_user_valid(seller)):
        return {"ERROR": "User not validated"}
    image_urls = await images_to_links(product.images)
    if (not image_urls):
        return {"status": "failure", "message": f"Error uploading image"}
    else:
        product.images = image_urls
    if (await upload_product_db(product)):
        return {"status": "success", "message": "Product uploaded successfully."}
    return {"status": "failure", "message": "Error uploading product"}
