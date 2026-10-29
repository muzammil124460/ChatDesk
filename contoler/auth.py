from authlib.integrations.starlette_client import OAuth
import os
from dotenv import load_dotenv
from fastapi import Request, HTTPException
load_dotenv()



oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)


async def login_fun(request):
    redirect_to = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(
    request,
    redirect_to,
)




async def call_back_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Google authentication failed",
        ) from exc

    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=400,
            detail="Google user information not found",
        )

    return {
        "message": "Google login successful",
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "google_id": user_info.get("sub"),
    }


