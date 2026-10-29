from fastapi import APIRouter,Request
from contoler.auth import login_fun,call_back_google
auth = APIRouter(prefix="/auth")




@auth.get("/login", name="google_login")
async def login(request: Request):
    return await login_fun(request)

@auth.get("/google/callback", name="google_callback")
async def google_call_back(request: Request):
    return await call_back_google(request)
