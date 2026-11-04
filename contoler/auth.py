from authlib.integrations.starlette_client import OAuth
import os
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from db.user import User
import jwt
from datetime import datetime, timedelta, timezone
import os
from pydantic_model.auth import token
load_dotenv()



oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": (
            "openid email profile "
            "https://www.googleapis.com/auth/gmail.modify"
        )},
)







def create_access_token(data:dict):

    token_data = data

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    token_data.update({"exp": expire})

    token = jwt.encode(
        token_data,
        key=os.getenv("SECRET_KEY"),
        algorithm=os.getenv("ALGORITHM")
    )

    

    return token





async def login_fun(request):
    redirect_to = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(
    request,
    redirect_to,
     access_type="offline",
        prompt="consent"
)


async def call_back_google(request, db):

    try:
        google_token = await oauth.google.authorize_access_token(request)

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Google authentication failed"
        ) from exc

    user_info = google_token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=400,
            detail="Google user information not found"
        )

    if not user_info.get("email_verified"):
        raise HTTPException(
            status_code=400,
            detail="User email not verified"
        )

    google_id = user_info.get("sub")

    try:
        user = db.query(User).filter(
            User.google_id == google_id
        ).first()

        is_new_user = False

        if not user:
            user = User(
                name=user_info.get("name"),
                email=user_info.get("email"),
                google_id=google_id,
                profile_picture=user_info.get("picture")
            )

            db.add(user)
            is_new_user = True

        # Save Gmail OAuth credentials
        user.access_token = google_token.get("access_token")

        # Google may not return refresh_token on every login.
        new_refresh_token = google_token.get("refresh_token")

        if new_refresh_token:
            user.refresh_token = new_refresh_token

        user.expires_at = google_token.get("expires_at")
        user.token_type = google_token.get("token_type")
        user.scope = google_token.get("scope")

        db.commit()
        db.refresh(user)

        app_token = create_access_token({
            "id": user.id,
            "email": user.email,
            "name": user.name
        })

        return {
            "message": "Login successful",
            "status": "register" if is_new_user else "login",
            "token": app_token
        }

    except Exception as err:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="User authentication failed"
        ) from err