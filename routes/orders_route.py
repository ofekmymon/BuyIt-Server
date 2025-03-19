from fastapi import APIRouter, HTTPException
from schemas.orders_schemas import DeleteOrderSchema, OrderSchema
from schemas.user_schemas import GetUserDataSchema
from services.orders_service import upload_orders, update_cart, fetch_order, delete_orders

router = APIRouter(prefix="/orders")


@router.post("/upload-order")
async def upload_order(order: OrderSchema):
    # this function will upload the order given to the db, find the item in the user cart and remove it
    try:
        result = await upload_orders(order)
        if not result:
            raise HTTPException(
                status_code=400, detail="Unable to complete order")
        update_cart_result = await update_cart(order)
        if not update_cart_result:
            raise HTTPException(
                status_code=400, detail="Unable to update cart")
        return {"status": "success"}
    except Exception as e:
        print(str(e), "failed to upload order")
        raise HTTPException(status_code=400, detail="Unable to complete order")


@router.post("/fetch-orders")
async def fetch_orders(data: GetUserDataSchema):
    # get orders from user
    orders = await fetch_order(data)
    if orders:
        return {"status": "success", "orders": orders["orders"]}
    print("failed to fetch orders")
    raise HTTPException(status_code=400, detail="Bad Request")


@router.post("/delete-order")
async def delete_order(data: DeleteOrderSchema):
    result = delete_orders(data)
    if result:
        return {"status": "success"}
    return {"status": "failure"}
