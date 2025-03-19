import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_mail import ConnectionConfig
from fastapi.middleware.cors import CORSMiddleware
import boto3
import motor.motor_asyncio

from routes.auth_route import router as auth_router
from routes.cart_route import router as cart_router
from routes.orders_route import router as orders_router
from routes.products_route import router as products_router
from routes.user_route import router as user_router
from routes.user_history_route import router as user_history_router
from routes.review_route import router as review_router


load_dotenv()
# db
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_DB_URL"))
db = client.get_database("BuyIt")

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
        "http://localhost:3000",
        # "https://buy-it-ofek-mymon.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(products_router)
app.include_router(user_router)
app.include_router(user_history_router)
app.include_router(review_router)


@app.get("/")
def connection():
    return {"message": "Connected Successfully"}
