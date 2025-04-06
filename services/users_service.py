import os
from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
import jwt
from mongomanager import users_collection
from microservices.auth_microservice import generate_access_token, generate_refresh_token, validate_user_details
from microservices.users_microservice import compare_passwords, find_user_by_email, hash_password, save_user, createCookie


async def signup_user(user):
    user_data = user.dict()
    user_data["password"] = hash_password(user_data["password"])
    if not validate_user_details(user):
        raise HTTPException(status_code=400, detail="Invalid Details")
    existing_user = await find_user_by_email(user_data["email"])
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    await save_user()


async def signin_user(user, response):
    # if fails find_user_by_email returns an httpexception to the user
    found_user = await find_user_by_email(user.email)
    if found_user == None:
        raise HTTPException(status_code=404, detail="User Not Found")
    compare_passwords(user.password, found_user["password"])
    refresh_token = generate_refresh_token(
        found_user["email"], found_user["verified"], user.remember)
    createCookie(user.remember, response, refresh_token)
    access_token = generate_access_token(
        found_user["email"], found_user["verified"])
    return {"message": f"Logged in as {found_user['name']}", "access_token": access_token, "user": found_user}


async def signout_user(request, response):
    if "refresh_token" in request.cookies:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="None",
            path="/",
        )
        return True
    return False


async def get_user(token):
    try:
        payload = jwt.decode(token, os.getenv(
            "JWT_SECRET_ACCESS"), algorithms="HS256")
        result = await users_collection.find_one({"email": payload["sub"]})
        user = {
            "_id": str(result["_id"]),
            "email": result["email"],
            "verified": result["verified"],
            "name": result["name"],
            "address": result["address"]
        }
        return user
    except:
        return None


async def edit_user(new_data):
    try:
        query_filter = {"email": new_data.userValidationEmail}
        update_operation = {
            '$set': {'name': new_data.name, 'address': new_data.address}}
        await users_collection.update_one(query_filter, update_operation)
        return True
    except:
        return False


async def check_if_user_valid(username: str):
    user = await users_collection.find_one({'name': username})
    if user:
        return user.get("verified", False)
    return False
