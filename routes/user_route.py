import json
from fastapi import APIRouter, HTTPException, Response, Request
from schemas.user_schemas import EditDetailsSchema, SignInSchema, UserSchema
from services.users_service import signup_user, signin_user, signout_user, get_user, edit_user

router = APIRouter(prefix="/user")


@router.post("/signup")
async def signup(user: UserSchema):
    signup_user(user)
    return {"message": "Signup successful"}


@router.post("/signin")
async def signin(user: SignInSchema, response: Response):
    result = signin_user(user, response)
    return result


@router.get("/signout")
async def signout(response: Response):
    result = signout_user(response)
    return result


@router.post("/fetch-user")
async def fetch_user(request: Request):
    # get basic user information
    raw_body = await request.body()  # Get the raw body as bytes
    json_body = json.loads(raw_body)
    access_token = json_body.get("access_token")
    if (not access_token):
        return {"status": "failure", "status_code": 403, "user": None}
    user = get_user(access_token)
    if (user):
        return {"status": "sucess", "status_code": 200, "user": user}
    print("failed to retrieve user with access token, refreshing..")
    return {"status": "failure", "status_code": 404, "user": None}


@router.post("/edit-user-details")
async def editDetails(editRequest: EditDetailsSchema):
    # edits user details
    result = await edit_user()
    if (result):
        return {'status': 'success'}
    return {'status': 'failure'}
