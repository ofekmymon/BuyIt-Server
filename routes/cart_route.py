from fastapi import APIRouter, HTTPException

from schemas.cart_schemas import MutateCartSchema, SaveLocalCart
from schemas.user_schemas import GetUserDataSchema
from services.cart_service import update_cart_from_local, get_user_cart, add_to_cart, delete_item_in_cart

router = APIRouter(prefix="/cart")


@router.post("/save-local-cart")
async def save_local_cart(request: SaveLocalCart):
    # this function saves the cart that a user had before logged,2 in the db
    result = await update_cart_from_local(request)
    if result.modified_count:
        return {"status": "success", "message": "Items added successfuly."}
    return {"status": "failiure", "message": "Items were not added"}


@router.post("/get-cart")
async def get_cart(user_data: GetUserDataSchema):
    # get cart from user db
    cart = await get_user_cart(user_data)
    return {"status": "success", "cart": cart}


@router.post("/add-cart-item")
async def add_cart_item(req: MutateCartSchema):
    # adds item to cart. if item already in cart, increase its quantity
    result = await add_to_cart(req)
    if result:
        return {"status": "success"}
    print("Error adding cart item: ")
    return {"status": "failure"}


@router.post("/delete-cart-item")
async def delete_cart_item(req: MutateCartSchema):
    # delete item from cart
    result = await delete_item_in_cart(req)
    if result:
        return {"status": "success"}
    print("Error deleting cart item")
    return {"status": "failure"}
