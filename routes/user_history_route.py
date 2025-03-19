
from fastapi import APIRouter
from schemas.product_schemas import ProductsFromTagsSchema
from schemas.user_schemas import GetUserDataSchema
from services.user_history_service import *

router = APIRouter(prefix="/user-history")


@router.get("/add-search-history")
async def save_search_history(user_id: str, search_query: str):
    # save search history to db
    result = await save_user_search_history(user_id, search_query)
    return result


@router.get("/save-product-history")
async def save_product_history(category: str, user_id: str):
    # save the last product and category history the user visited.
    result = await save_user_product_history(category, user_id)
    return result


@router.get("/fetch-product-history")
async def fetch_product_history(user_id: str):
    result = await fetch_user_product_history(user_id)
    if result:
        return result
    return False


@router.get("/fetch-search-history")
async def fetch_search_history(user_id: str):
    result = await fetch_user_search_history(user_id)
    if result:
        return result


@router.get("/order-history-tags")
async def order_history_tags(user_id: str):
    # request to fetch products based on product history
    result = await get_order_tags(user_id)
    if result:
        return result


@router.post("/fetch-order-history")
async def fetch_order_history(data: GetUserDataSchema):
    result = await get_order_history(data)
    if result:
        return result
