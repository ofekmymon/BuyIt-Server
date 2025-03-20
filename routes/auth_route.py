from fastapi import APIRouter, BackgroundTasks, Request
from schemas.user_schemas import EmailSchema, VerificationCodeSchema
from services.auth_service import *

router = APIRouter(prefix="/auth")


@router.get("/generate-access-token")
def generate_access_token(request: Request):
    new_token = create_access_token(request)
    if new_token:
        return {"status_code": 200, "status": "success", "token": new_token}
    else:
        return {"status_code": 401, "status": "failure", "token": None}


@router.get("/validate-refresh-token")
def verify_refresh_token(request: Request):
    result = validate_refresh_token(request)
    if result:
        return {"status_code": 200, "status": "success"}
    return {"status_code": 400, "status": "Failure"}


@router.post("/validate-access-token")
def verify_access_token(access_token: str):
    result = validate_access_token(access_token)
    if result == 200:
        return {"status_code": 200, "status": "valid"}
    return {"status_code": result, "status": "invalid"}


@router.post("/get-verification-code")
# function that sends a random verification code via email and saves it on temp db
async def validate_email(background_tasks: BackgroundTasks, email_data: EmailSchema):
    result = await get_verification_code(background_tasks, email_data.email)
    if result:
        return {"status": "success", "message": "Verification email sent."}


@router.post("/verify-verification-code")
# function that verifies the code from the db
async def validate_code(validation_data: VerificationCodeSchema):
    result = await verify_verification_code(validation_data)
    return result
