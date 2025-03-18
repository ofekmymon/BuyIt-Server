import os
from dotenv import load_dotenv
import jwt
import random
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Response, Request, BackgroundTasks, Query
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from rapidfuzz import process, utils
from datetime import datetime, timedelta, timezone
import bcrypt
from typing import Optional, List
import json
import boto3
import time
import uuid
from bson import ObjectId
from io import BytesIO
import motor.motor_asyncio
from email_validator import validate_email as email_verification, EmailNotValidError
import re
from schemas.user_schemas import *
from schemas.cart_schemas import *
from schemas.orders_schemas import *
from schemas.product_schemas import *
from schemas.product_schemas import *
from schemas.review_schemas import *
from schemas.user_history_schemas import *

load_dotenv()
# db
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_DB_URL"))
db = client.get_database("BuyIt")
# user db details TAKEN
users_collection = db.get_collection("Users")
validation_token_collection = db.get_collection("Tokens")
product_collection = db.get_collection("Products")
orders_collection = db.get_collection("Orders")
user_visited_collection = db.get_collection("User_Last_Visited")
order_history_collection = db.get_collection("User_Order_History")
user_search_history_collection = db.get_collection("User_Search_History")


# AWS S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASSWORD"),
    MAIL_FROM=f"{os.getenv('EMAIL_USERNAME')}@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME='BuyIt',
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    VALIDATE_CERTS=True,
)


##
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # Replace with your frontend's URL
    allow_origins=[
        # development
        # "http://localhost:3000",
        "https://buy-it-ofek-mymon.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def fetch_product_tags(order_ids: List[str]):
    # fetches a list of all of the tags in the past orders
    obj_ids = list(map(ObjectId, order_ids))
    # fetch tags from the ids
    query_result = await product_collection.find({"_id": {"$in": obj_ids}}, {"tags": 1, "_id": 0}).to_list(None)
    result = []
    for tags in query_result:
        result.append(" ".join(tags["tags"]))
    return result


async def get_products_from_tags(tags: List[str]):
    # this function gets a list of tags and hands out products that fit these tags
    try:
        all_products = await product_collection.find({}, {"_id": 1, "tags": 1}).to_list(None)
        matching_ids = []
        for product in all_products:
            for tag_string in tags:
                product_score = process.extractOne(
                    tag_string, [tag for tag in product["tags"]], processor=utils.default_process)
                if product_score[2] <= 1 and product_score[1] >= 80:
                    matching_ids.append(product["_id"])
        if len(matching_ids) < 4:
            return []
        products = await product_collection.find({"_id": {"$in": matching_ids}}).to_list(None)
        # fetch 4 random products.
        if len(matching_ids) >= 4:
            products_to_send = random.sample(products, 4)
            # convert id to string because of python
            for product in products_to_send:
                product["_id"] = str(product["_id"])
            return products_to_send
        return []
    except Exception as e:
        print(str(e), " failed to get products from tags")
        return []


async def add_to_search_history(query: str, user_id: str):
    searched_at = datetime.now(timezone.utc)
    try:
        result = await user_search_history_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "searches": {
                        "$each": [{"query": query, "searched_at": searched_at}],
                        "$position": 0,
                        "$slice": 10  # limited to store the last 10 searches
                    }
                }
            },
            upsert=True
        )
        if result:
            return True
        return False
    except:
        raise HTTPException(
            status_code=400, detail="Failed to save search history")


async def check_if_user_valid(username: str):
    user = await users_collection.find_one({'name': username})
    if user:
        return user.verified
    return False


@app.get("/")
def connection():
    return {"message": "Connected Successfully"}


@app.get("/query-products-by-category")
async def query_products_by_category(category: str, number: int):
    # get a specific amount of different products from based on their category
    result = await product_collection.find({"category": category}).to_list(None)
    if not result:
        raise HTTPException(
            status_code=404, detail="No products found for the given category")

    sample_size = min(len(result), number)
    products_to_send = random.sample(result, sample_size)
    for product in products_to_send:
        product["_id"] = str(product["_id"])
    return {"status": "success", "result": products_to_send}


@app.get("/fetch-product")
async def fetch_product(id: str):
    # fetch product data using its id
    try:
        product = await product_collection.find_one({"_id": ObjectId(id)})
        if not product:
            raise HTTPException(
                status_code=404, detail="No product found for the given id")
        product["_id"] = str(product["_id"])
        return {"status": "success", "product": product}
    except:
        return {"status": "failure", "error": "Unable to query product"}


@app.post("/upload-review")
async def upload_review(review: ReviewSchema):
    # updates the db if theres a review with the same name to edit it. otherwise push it to the list of reviews
    try:
        update_result = await product_collection.update_one(
            {"_id": ObjectId(review.product_id),
             "ratings.user_id": review.user_id},
            {
                "$set": {
                    "ratings.$.details": review.review_text,
                    "ratings.$.rating": review.rating,
                }
            },
        )
        if update_result.modified_count == 0:
            # If no review was updated, push a new review
            insert_result = await product_collection.update_one(
                {"_id": ObjectId(review.product_id)},
                {
                    "$push": {
                        "ratings": {
                            "username": review.username,
                            "user_id": review.user_id,
                            "details": review.review_text,
                            "rating": review.rating,
                        }
                    }
                }
            )
            if insert_result.modified_count == 0:
                # error product probably not exists or in the db
                raise HTTPException(
                    status_code=404, detail="Product not found or no changes made")
        return {"message": "Review added successfully", "status": "success"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload review")


@app.post("/save-local-cart")
async def save_local_cart(request: SaveLocalCart):
    # this function saves the cart that a user had before logged,2 in the db
    user = await users_collection.find_one({"email": request.email})
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
    if result.modified_count:
        return {"status": "success", "message": "Items added successfuly."}
    return {"status": "failiure", "message": "Items were not added"}


@app.post("/get-cart")
async def get_cart(user_data: GetUserDataSchema):
    # get cart from user db
    user = await users_collection.find_one({"_id": ObjectId(user_data.id)})
    if user:
        return {"status": "success", "cart": user["cart"]}
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/add-cart-item")
async def add_cart_item(req: MutateCartSchema):
    # adds item to cart. if item already in cart, increase its quantity
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
        return {"status": "success"}

    except Exception as e:
        print("Error adding cart item: ", e)
        return {"status": "failure"}


@app.post("/delete-cart-item")
async def delete_cart_item(req: MutateCartSchema):
    # delete item from cart
    try:
        user = await users_collection.find_one({"email": req.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        current_cart = user.get("cart", [])
        updated_cart = [
            item for item in current_cart if item["product_id"] != req.product.product_id]
        await users_collection.update_one({"email": req.email}, {"$set": {"cart": updated_cart}})
        return {"status": "success"}

    except Exception as e:
        print("Error deleting cart item: ", e)
        return {"status": "failure"}


@app.get("/products-query")
async def get_products(category: Optional[str] = None, search: Optional[str] = None, page: int = Query(1), per_page: int = 8, sort_by: Optional[str] = None, rnd: Optional[bool] = False):
    # this function is being used with infinite scrolling of react query.
    # create a search query based on category or tags or name
    query = {}
    relevance_map = {}
    if search:
        # filter products by the search
        all_products = await product_collection.find({}, {"_id": 1, "name": 1, "tags": 1, "category": 1}).to_list(None)
        matched_ids = []
        for product in all_products:
            product_score = process.extractOne(search,
                                               [word for word in product["name"].split() if len(word) > 2] + [product["category"]] + [tag for tag in product["tags"] if len(tag) > 1], processor=utils.default_process)
            if product_score[1] > 85:
                matched_ids.append(product["_id"])
                relevance_map[str(product["_id"])] = product_score[1]
        if rnd:
            matched_ids = random.sample(matched_ids, 4)
        query["_id"] = {"$in": matched_ids}

    if category:
        query["category"] = category

    total_products = await product_collection.count_documents(query)
    # using the page, decide on how many products to skip over that were already fetched
    skip_count = (page - 1) * per_page
    # if sort by relevence, keep the order the same
    sort_option = {"_id": 1}
    match sort_by:
        case 'high-to-low':
            sort_option = {"price": -1, "_id": 1}
        case 'low-to-high':
            sort_option = {"price": 1, "_id": 1}
        case 'ratings':
            sort_option = {"average_rating": -1, "_id": 1}
        case 'relevence' if search:
            sort_option = {"relevence_score": -1, "_id": 1}

    # pipeline for custom searching the average ratings and by relevency:
    pipeline = [
        {"$match": query},
        {"$unwind": {
            "path": "$ratings",
            "preserveNullAndEmptyArrays": True}
         },
        {
            "$group": {
                "_id": "$_id",
                "name": {"$first": "$name"},
                "price": {"$first": "$price"},
                "seller": {"$first": "$seller"},
                "images": {"$first": "$images"},
                "ratings": {"$push": "$ratings"},
                "average_rating": {"$avg": "$ratings.rating"},
            }
        },
        {
            "$addFields": {
                "relevence_score": {
                    "$getField": {
                        "field": {"$toString": "$_id"},
                        "input": relevance_map
                    }
                }
            },
        },
        {"$sort": sort_option},  # Apply sorting
        {"$skip": skip_count},  # skip the sent pages
        {"$limit": per_page}
    ]
    products = await product_collection.aggregate(pipeline).to_list(length=per_page)
    # change id to str so python could handle it
    for product in products:
        product["_id"] = str(product["_id"])
    # next page will be none if skip and the amount of pages is more than total products
    # ( if theres no products left)
    next_page = page + 1 if skip_count + per_page < total_products else None
    return {"products": products, "nextPage": next_page, "length": total_products}


@app.get("/add-search-history")
async def save_search_history(user_id: str, search_query: str):
    # save search history to db
    try:
        result = await user_search_history_collection.find_one({"user_id": user_id})
        if result:
            temp_visited = result["search_queries"]
            if search_query in temp_visited:
                # search queries are worth 5 points of relevency
                temp_visited[search_query] += 5
            else:
                temp_visited[search_query] = 5
            await user_search_history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"search_queries": temp_visited}}
            )
        if not result:
            await user_search_history_collection.insert_one({"user_id": user_id, "search_queries": {search_query: 1}})
        return True
    except Exception as e:
        return False


@app.post("/upload-order")
async def upload_order(order: OrderSchema):
    # this function will upload the order given to the db, find the item in the user cart and remove it
    order_dict = order.dict()
    # take only the dat e of the time
    order_dict["order_date"] = datetime.now(
        timezone.utc).date().strftime('%Y-%m-%d')
    try:
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
        # find user and update item in cart
        await users_collection.update_one(
            {"_id": ObjectId(order_dict["user_id"]),
             "cart.product_id": order_dict["product_id"]},
            # decrease item quantity
            {"$inc": {"cart.$.quantity": -order_dict["quantity"]}})

        # Now, remove items where quantity is 0
        await users_collection.update_one(
            {"_id": ObjectId(order_dict["user_id"])},
            {"$pull": {"cart": {"quantity": {"$lte": 0}}}}
        )

        return {"status": "success"}

    except Exception as e:
        print(str(e), "failed to upload order")
        raise HTTPException(status_code=400, detail="Unable to complete order")


@app.post("/fetch-orders")
async def fetch_orders(data: GetUserDataSchema):
    # get orders from user
    try:
        orders_query = await orders_collection.find_one({"user_id": data.id})
        if orders_query == None:
            return {"status": "success", "orders": []}
        orders_query["_id"] = str(orders_query["_id"])
        return {"status": "success", "orders": orders_query["orders"]}
    except Exception as e:
        print(str(e), "failed to fetch orders")
        raise HTTPException(status_code=400, detail="Bad Request")


@app.get("/save-product-history")
async def save_product_history(category: str, user_id: str):
    # save the last product and category history the user visited.
    try:
        result = await user_visited_collection.find_one({"user_id": user_id})
        if result:
            temp_visited = result["categories_visited"]
            if category in temp_visited:
                # categories and products visited are worth 1 point
                temp_visited[category] += 1
            else:
                temp_visited[category] = 1
            await user_visited_collection.update_one(
                {"user_id": user_id},
                {"$set": {"categories_visited": temp_visited}}
            )
        if not result:
            await user_visited_collection.insert_one({"user_id": user_id, "categories_visited": {category: 1}})
        return True
    except Exception as e:
        print(str(e), "failed to save product history")
        raise HTTPException(
            status_code=400, detail="Failed to save search history ")


@app.get("/fetch-product-history")
async def fetch_product_history(user_id: str):
    # fetches product history
    try:
        result = await user_visited_collection.find_one({"user_id": user_id})
        if result:
            categories = result["categories_visited"]
            return {"status": "success", "history": categories}
        return {"status": "failure", "history": []}
    except Exception as e:
        print(str(e), "failed to fetch product history")
        return False


@app.get("/fetch-search-history")
async def fetch_search_history(user_id: str):
    # fetches search history

    try:
        result = await user_search_history_collection.find_one({"user_id": user_id})
        if result:
            search_queries = result["search_queries"]
            return {"status": "success", "history": search_queries}
        return {"status": "failure", "history": []}
    except Exception as e:
        print(str(e), "failed to fetch search history")
        raise HTTPException(
            status_code=400, detail="Failed to save search history ")


@app.get("/order-history-tags")
async def order_history_tags(user_id: str):
    # request to fetch products based on product history
    try:
        result = await order_history_collection.find_one({"user_id": user_id})
        if result:
            order_ids = [order["product_id"] for order in result["orders"]]
            if len(order_ids) > 0:
                tag_list = await fetch_product_tags(order_ids)
                test = await get_products_from_tags(tag_list)
                if len(test) >= 4:
                    return {"status": "success", "tags": tag_list}
                return {"status": "failure", "tags": [], "details": "No sufficient products"}
            return {"status": "failure", "tags": [], "details": "No History Found"}
    except Exception as e:
        print(str(e), "failed to fetch history tags")
    raise HTTPException(
        status_code=400, detail="Could Not Fetch Order History Tags")


@app.post("/search-products-with-tags")
async def fetch_products_with_tags(data: ProductsFromTagsSchema):
    # gets tags and searches products
    try:
        tags = data.tags
        result = await get_products_from_tags(tags)
        if len(result) >= 4:
            return {"status": "success", "products": result}
        return {"status": "failure", "products": [], "details": "could not find sufficient products"}
    except Exception as e:
        print(str(e), "failed to search products with tags")
        raise HTTPException(
            status_code=400, detail="Could Not Fetch Products")


@app.post("/delete-order")
async def delete_order(data: DeleteOrderSchema):
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
        return {"status": "success"}
    return {"status": "failure"}


@app.post("/fetch-order-history")
async def fetch_order_history(data: GetUserDataSchema):
    user_id = data.id
    result = await order_history_collection.find_one({"user_id": user_id})
    if result:
        return {"status": "success", "orders": result["orders"]}
    return {"status": "failure", "details": "No order history found", "orders": []}
