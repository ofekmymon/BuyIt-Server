import random
import time
from typing import List
from mongomanager import product_collection
from rapidfuzz import process, utils


def generate_key():
    return str(int(time.time() * 1000)) + "_" + str(random.randint(100000000, 999999999))


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
