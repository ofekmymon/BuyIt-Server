import os
import motor.motor_asyncio


client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_DB_URL"))
db = client.get_database("BuyIt")

users_collection = db.get_collection("Users")
validation_token_collection = db.get_collection("Tokens")
product_collection = db.get_collection("Products")
orders_collection = db.get_collection("Orders")
user_visited_collection = db.get_collection("User_Last_Visited")
order_history_collection = db.get_collection("User_Order_History")
user_search_history_collection = db.get_collection("User_Search_History")
