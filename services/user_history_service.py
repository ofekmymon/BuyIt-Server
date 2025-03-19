from fastapi import HTTPException
from microservices.product_microservice import get_products_from_tags
from mongomanager import user_search_history_collection, user_visited_collection, order_history_collection
from microservices.user_history_micoservice import *


async def save_user_search_history(user_id, search_query):
    # save searchwords the user searched for and give them 5 point
    try:
        result = await user_search_history_collection.find_one({"user_id": user_id})
        if result:
            temp_visited = result["search_queries"]
            if search_query in temp_visited:
                # search queries are worth 5 points of relevancy
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


async def save_user_product_history(category, user_id):
    # save product categories the user visted and give them 1 point
    try:
        result = await user_visited_collection.find_one({"user_id": user_id})
        if result:
            temp_visited = result["categories_visited"]
            if category in temp_visited:
                # categories and products visited are worth 1 point of relevancy
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


async def fetch_user_product_history(user_id):
    # fetches product history
    try:
        result = await user_visited_collection.find_one({"user_id": user_id})
        if result:
            categories = result["categories_visited"]
            return categories
        return []
    except Exception as e:
        print(str(e), "failed to fetch product history")
        return None


async def fetch_user_search_history(user_id):
    # fetches search history
    try:
        result = await user_search_history_collection.find_one({"user_id": user_id})
        if result:
            search_queries = result["search_queries"]
            return search_queries
        return []
    except Exception as e:
        print(str(e), "failed to fetch search history")
        raise HTTPException(
            status_code=400, detail="Failed to save search history ")


async def get_order_tags(user_id):
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


async def get_products_using_tags(data):
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


async def get_order_history(data):
    user_id = data.id
    result = await order_history_collection.find_one({"user_id": user_id})
    if result:
        return {"status": "success", "orders": result["orders"]}
    return {"status": "failure", "details": "No order history found", "orders": []}
