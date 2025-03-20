import bcrypt
from fastapi import HTTPException
from mongomanager import users_collection


async def find_user_by_email(email: str):
    user = await users_collection.find_one({'email': email})
    if user:
        user["_id"] = str(user["_id"])
    return user


def hash_password(password: str) -> str:
    encrypt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), encrypt)
    return hashed.decode('utf-8')


def compare_passwords(password: str, hashed: str):
    if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')):
        return True
    else:
        raise HTTPException(status_code=404, detail="User Not Found")


async def save_user(user_data):
    try:
        await users_collection.insert_one(user_data)
    except Exception as e:
        print(f"Error saving user ${e}")


def createCookie(remember, response, refresh_token):
    cookie_age = 15 * 24 * 60 * 60 if remember else 2 * \
        60 * 60  # 15 days or 2 hours in seconds
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
        max_age=cookie_age
    )
