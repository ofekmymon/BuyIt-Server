from io import BytesIO
import random
from bson import ObjectId
from rapidfuzz import process, utils
from fastapi import HTTPException
from microservices.product_microservice import generate_key, get_products_from_tags
from mongomanager import product_collection
from schemas.product_schemas import BUCKET_NAME, s3


async def upload_product_db(product):
    try:
        # holds the urls to be saved in the db with the product
        product_data = product.dict()
        await product_collection.insert_one(product_data)
        return True
    except Exception as e:
        return False


async def get_product(id: str):
    try:
        product = await product_collection.find_one({"_id": ObjectId(id)})
        if not product:
            raise HTTPException(
                status_code=404, detail="No product found for the given id")
        product["_id"] = str(product["_id"])
        return product
    except:
        return None


async def images_to_links(images):
    image_urls = []
    for image in images:
        key = generate_key()
        try:
            image_content = await image.read()
            # Create a file-like object from the bytes
            file_like_object = BytesIO(image_content)
            s3.upload_fileobj(file_like_object, BUCKET_NAME, key)
            print(f"Successfully uploaded: {image.filename}")
            image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
            image_urls.append(image_url)
        except Exception as e:
            return False
    return image_urls


async def query_product_by_category(category, number):
    # get a specific amount of different products from based on their category
    result = await product_collection.find({"category": category}).to_list(None)
    if not result:
        raise HTTPException(
            status_code=404, detail="No products found for the given category")
    sample_size = min(len(result), number)
    products_to_send = random.sample(result, sample_size)
    for product in products_to_send:
        product["_id"] = str(product["_id"])
    return products_to_send


async def get_search_query(search, rnd, category):
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
    return query, relevance_map


async def get_relevant_products(query):
    total_products = await product_collection.count_documents(query)
    return total_products


async def build_product_query_pipeline(query, relevance_map, sort_option, skip_count, per_page):
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
    return pipeline


def get_sort_option(sort_by, search):
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
    return sort_option


async def product_pipeline(pipeline, per_page):
    products = await product_collection.aggregate(pipeline).to_list(length=per_page)
    # change id to str so python could handle it
    for product in products:
        product["_id"] = str(product["_id"])
    return products


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
