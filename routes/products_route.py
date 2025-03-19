import json
from typing import List, Optional
from fastapi import APIRouter, File, Form, Query, UploadFile
from services.products_service import *
from services.users_service import check_if_user_valid
from schemas.product_schemas import ProductSchema, ProductsFromTagsSchema


router = APIRouter(prefix="/products")


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
    if not image_urls:
        return {"status": "failure", "message": f"Error uploading image"}
    else:
        product.images = image_urls
    if (await upload_product_db(product)):
        return {"status": "success", "message": "Product uploaded successfully."}
    return {"status": "failure", "message": "Error uploading product"}


@router.get("/query-products-by-category")
async def query_products_by_category(category: str, number: int):
    # get a specific amount of different products from based on their category
    result = await query_product_by_category(category, number)
    return {"status": "success", "result": result}


@router.get("/fetch-product")
async def fetch_product(id: str):
    # fetch product data using its id
    product = await fetch_product(id)
    if product:
        return {"status": "success", "product": product}
    return {"status": "failure", "error": "Unable to query product"}


@router.get("/products-query")
async def get_products(category: Optional[str] = None, search: Optional[str] = None, page: int = Query(1), per_page: int = 8, sort_by: Optional[str] = None, rnd: Optional[bool] = False):
    # this function is being used with infinite scrolling of react query.
    # create a search query based on category or tags or name
    query, relevance_map = await get_search_query(search, rnd, category)
    total_products = await get_relevant_products(query)
    # using the page, decide on how many products to skip over that were already fetched
    skip_count = (page - 1) * per_page
    # if sort by relevence, keep the order the same
    sort_option = get_sort_option(sort_by, search)
    # pipeline for custom searching the average ratings and by relevency:
    pipeline = await build_product_query_pipeline(query, relevance_map, sort_option, skip_count, per_page)
    products = await product_pipeline(pipeline, per_page)
    # ( if theres no products left)
    next_page = page + 1 if skip_count + per_page < total_products else None
    return {"products": products, "nextPage": next_page, "length": total_products}


@router.post("/search-products-with-tags")
async def fetch_products_with_tags(data: ProductsFromTagsSchema):
    # gets tags and searches products
    result = await get_products_using_tags(data)
    if result:
        return result
