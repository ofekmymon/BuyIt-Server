import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_mail import ConnectionConfig
from fastapi.middleware.cors import CORSMiddleware
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
##
app = FastAPI()


app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(products_router)
app.include_router(user_router)
app.include_router(user_history_router)
app.include_router(review_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific frontend URL
    allow_credentials=True,  # Allow cookies & auth headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
def connection():
    return {"message": "Connected Successfully"}
