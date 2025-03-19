from bson import ObjectId
from mongomanager import product_collection


async def update_review(review):
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
    return update_result


async def add_review(review):
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
    return insert_result
