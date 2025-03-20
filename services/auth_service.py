from datetime import datetime, timedelta, timezone
import os
from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema
import jwt
from microservices.auth_microservice import generate_access_token, generate_verification_code
from mongomanager import validation_token_collection, users_collection
from schemas.auth_schemas import conf


def validate_refresh_token(request):
    refresh_token = request.cookies.get("refresh_token")
    try:
        if (jwt.decode(refresh_token, os.getenv("JWT_SECRET_REFRESH"), algorithms="HS256")):
            return True
        return False
    except:
        return True


def validate_access_token(token):
    try:
        if (jwt.decode(token, os.getenv("JWT_SECRET_ACCESS"), algorithms="HS256", options={"verify_exp": True})):
            return 200
        return 401
    except:
        return 400


def create_access_token(request):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            print("No refresh token found.")
            return None
        refresh_payload = jwt.decode(refresh_token.encode(), os.getenv(
            "JWT_SECRET_REFRESH"), algorithms="HS256")
        email = refresh_payload["sub"]
        verified = refresh_payload["verified"]
        new_token = generate_access_token(email, verified)
        return new_token
    except Exception as e:
        print(f"Error generating access token: ${e}")
        return None


async def get_verification_code(bg_task, email):
    try:
        code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=300)
        await validation_token_collection.update_one(
            {
                "email": email
            },
            {
                "$set": {
                    "email": email,
                    "code": code,
                    "expiresAfter": expires_at
                }
            },
            upsert=True  # create new doc if not exists
        )
        message = MessageSchema(
            subject="Your Verification Code",
            recipients=[email],  # List of recipient emails
            body=f"Your verification code is: {code}",
            subtype="plain"
        )
        # for email sending

        fm = FastMail(conf)
        bg_task.add_task(fm.send_message, message)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=403, detail=f"Error sending code: ${e}")


async def verify_verification_code(data):
    code_data = await validation_token_collection.find_one({"email": data.email})
    # if code expired
    if code_data is None:
        return {"status": "failure", "message": "Code expired or invalid."}
    # if code valid verify user and delete the code from db
    if code_data["code"] == data.code:
        await validation_token_collection.delete_one({"email": data.email})
        result = await users_collection.update_one({"email": data.email}, {"$set": {"verified": True}})
        if result.modified_count:
            return {"status": "success", "message": "Code validated successfuly."}
        else:
            return {"status": "failure", "message": "Failed to validate client."}
    # if code invalid
    else:
        return {"status": "failure", "message": "Invalid code."}
