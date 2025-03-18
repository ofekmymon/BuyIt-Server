
from io import BytesIO
import json

from fastapi import HTTPException
from microservices.product_microservice import generate_key
from mongomanager import product_collection
from server import BUCKET_NAME, s3


async def upload_product_db(product):
    try:
        # holds the urls to be saved in the db with the product
        product_data = product.dict()
        await product_collection.insert_one(product_data)
        return True
    except Exception as e:
        return False


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
