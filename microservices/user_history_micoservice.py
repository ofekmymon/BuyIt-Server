import random
from typing import List
from bson import ObjectId
from mongomanager import product_collection


async def fetch_product_tags(order_ids: List[str]):
    # fetches a list of all of the tags in the past orders
    obj_ids = list(map(ObjectId, order_ids))
    # fetch tags from the ids
    query_result = await product_collection.find({"_id": {"$in": obj_ids}}, {"tags": 1, "_id": 0}).to_list(None)
    result = []
    for tags in query_result:
        result.append(" ".join(tags["tags"]))
    return result
