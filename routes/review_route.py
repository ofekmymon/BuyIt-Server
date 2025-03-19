from fastapi import APIRouter, HTTPException
from schemas.review_schemas import ReviewSchema
from services.review_service import update_review, add_review

router = APIRouter(prefix="/review")


@router.post("/upload-review")
async def upload_review(review: ReviewSchema):
    # updates the db if theres a review with the same name to edit it. otherwise push it to the list of reviews
    try:
        update_result = await update_review(review)
        if update_result.modified_count == 0:
            # If no review was updated, push a new review
            insert_result = await add_review(review)
            if insert_result.modified_count == 0:
                # error product probably not exists or in the db
                raise HTTPException(
                    status_code=404, detail="Product not found or no changes made")
        return {"message": "Review added successfully", "status": "success"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload review")
