from bson import ObjectId
from fastapi import HTTPException
from microservices.users_microservice import find_user_by_email
from mongomanager import users_collection


async def update_cart_from_local(request):
    # updates the user cart in the db from local cart when he logs in
    user = await find_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # fetch the cart from the user if exists or if not get an empty list
    current_cart = user.get("cart", [])
    # create a dict from the user.cart
    cart = {str(item["product_id"]): item["quantity"] for item in current_cart}
    for item in request.local_cart:
        if item.product_id in cart:
            cart[item.product_id] += item.quantity
        else:
            cart[item.product_id] = item.quantity
    # returns to list
    updated_cart = [{"product_id": id, "quantity": quantity}
                    for id, quantity in cart.items()]
    result = await users_collection.update_one({"email": request.email}, {"$set": {"cart": updated_cart}})
    return result


async def get_user_cart(user_data):
    user = await users_collection.find_one({"_id": ObjectId(user_data.id)})
    if user:
        return user["cart"]
    raise HTTPException(status_code=404, detail="User not found")


async def add_to_cart(req):
    # adds a new item to cart or increment an existing item
    try:
        user = await users_collection.find_one({"email": req.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        current_cart = user.get("cart", [])
        cart = {str(item["product_id"]): item["quantity"]
                for item in current_cart}
        if req.product.product_id in cart:
            cart[req.product.product_id] += req.product.quantity
        else:
            cart[req.product.product_id] = req.product.quantity
        # returns to list
        updated_cart = [{"product_id": id, "quantity": quantity}
                        for id, quantity in cart.items()]
        await users_collection.update_one({"email": req.email}, {"$set": {"cart": updated_cart}})
        return True

    except Exception as e:
        print("Error adding cart item: ", e)
        return False


async def delete_item_in_cart(req):
    try:
        user = await users_collection.find_one({"email": req.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_cart = user.get("cart", [])
        updated_cart = [
            item for item in current_cart if item["product_id"] != req.product.product_id]
        await users_collection.update_one({"email": req.email}, {"$set": {"cart": updated_cart}})
        return True
    except Exception as e:
        print("Error deleting cart item: ", e)
        return False
