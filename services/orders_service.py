from datetime import datetime, timezone
import uuid

from bson import ObjectId
from fastapi import HTTPException
from mongomanager import orders_collection, users_collection, order_history_collection


async def upload_orders(order):
    try:
        order_dict = order.dict()
        # take only the dat e of the time
        order_dict["order_date"] = datetime.now(
            timezone.utc).date().strftime('%Y-%m-%d')
        order_id = str(uuid.uuid4())
        await orders_collection.update_one(
            {"user_id": order_dict["user_id"]},
            {"$push": {
                "orders": {
                    "order_id": order_id,
                    "product_id": order_dict["product_id"],
                    "quantity": order_dict["quantity"],
                    "address": order_dict["address"],
                    "order_date": order_dict["order_date"],
                    "order_status": "Getting ready for shippping"
                }
            }},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error uploading order: ${e}")
        return False


async def update_cart(order):
    try:
        # find user and update item in cart
        order_dict = order.dict()
        await users_collection.update_one(
            {"_id": ObjectId(order_dict["user_id"]),
                "cart.product_id": order_dict["product_id"]},
            # decrease item quantity
            {"$inc": {"cart.$.quantity": -order_dict["quantity"]}})

        # remove items where quantity is 0
        await users_collection.update_one(
            {"_id": ObjectId(order_dict["user_id"])},
            {"$pull": {"cart": {"quantity": {"$lte": 0}}}}
        )
        return True
    except Exception as e:
        print(f"Error Updating cart: ${e}")
        return False


async def fetch_orders(data):
    # get orders from user
    try:
        orders_query = await orders_collection.find_one({"user_id": data.id})
        if orders_query == None:
            return {"status": "success", "orders": []}
        orders_query["_id"] = str(orders_query["_id"])
        return orders_query
    except Exception as e:
        print(str(e), "failed to fetch orders")
        raise HTTPException(status_code=400, detail="Bad Request")


async def delete_orders(data):
    result = await orders_collection.update_one({"user_id": data.user_id}, {"$pull": {"orders": {"order_id": data.order_id}}})
    if result.modified_count:
        # add to order history
        await order_history_collection.update_one(
            {"user_id": data.user_id},
            {
                "$push": {
                    "orders": {
                        "product_id": data.product_id,
                        "quantity": data.quantity,
                        "ordered_at": data.order_date
                    }
                }
            }, upsert=True
        )
        return True
    return False
