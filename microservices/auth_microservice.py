from datetime import datetime, timedelta, timezone
import os
import random
import re
import jwt
from email_validator import validate_email as email_verification, EmailNotValidError


def validate_user_details(user):
    # validates details before saving them
    if (3 > len(user.name) > 12):
        return False
    try:
        email_verification(user.email, check_deliverability=True)
    except EmailNotValidError as e:
        return False
    if (4 > len(user.password) > 12 or re.search(r'\s', user.password)):
        return False
    return True


def generate_refresh_token(email: str, verified: bool, rememberMe: bool):
    # Calculate expiration time
    expire = datetime.now(timezone.utc) + timedelta(
        days=15) if rememberMe else datetime.now(timezone.utc) + timedelta(hours=4)
    expire_timestamp = int(expire.timestamp())  # Convert to Unix timestamp
    # Payload
    to_encode = {"sub": email, "verified": verified, "exp": expire_timestamp}
    # Generate refresh token
    refresh_token = jwt.encode(to_encode, os.getenv(
        "JWT_SECRET_REFRESH"), algorithm="HS256")
    return refresh_token


def generate_access_token(email: str, verified: bool):
    # expiration time for the access token
    expire = datetime.now(timezone.utc) + timedelta(minutes=0.1)
    # payload
    to_encode = {"sub": email, "verified": verified, "exp": expire}
    access_token = jwt.encode(to_encode, os.getenv(
        "JWT_SECRET_ACCESS"), algorithm="HS256")
    return access_token


def generate_verification_code():
    return str(random.randint(100000, 999999))
