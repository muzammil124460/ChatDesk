from fastapi import APIRouter,Request,Depends
from sqlalchemy.orm import Session

from contoler.auth import login_fun,call_back_google
from db.connection import get_db




auth = APIRouter(prefix="/auth")




@auth.get("/login", name="google_login")
async def login(request: Request):
    return await login_fun(request)

@auth.get("/google/callback", name="google_callback")
async def google_call_back(request : Request,db:Session=Depends(get_db)):
    return await call_back_google(request,db)
