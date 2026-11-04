import os
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from db.user import User
from fastapi import Depends
from depends.is_authenticated import is_authenticated as is_auth_depends
from db.connection import get_db





def get_gmail_credentials(user_id:dict = Depends(is_auth_depends), db:Session=Depends(get_db) ):

    # 1. Database se user fetch 
    user_id = user_id["id"]
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 2. Check karo Google tokens available hain ya nahi
    if not user.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Google account needs to be connected again"
        )

    # 3. Google credentials object banao
    expiry = (
    datetime.fromtimestamp(
        user.expires_at,
        tz=timezone.utc
    ).replace(tzinfo=None)
    if user.expires_at else None
)


    credentials = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        scopes=user.scope.split() if user.scope else None,
        expiry=expiry
    )

    # 4. Access token expire hua hai ya nahi check karo
    if not credentials.valid:

        try:
            credentials.refresh(Request())

        except Exception as exc:
            raise HTTPException(
                status_code=401,
                detail="Google token refresh failed. Please reconnect your Google account."
            ) from exc

        # 5. New token database mein save karo
        user.access_token = credentials.token

        if credentials.refresh_token:
            user.refresh_token = credentials.refresh_token

        if credentials.expiry:
            user.expires_at = int(credentials.expiry.timestamp())

        db.commit()
        db.refresh(user)

    # 6. Valid credentials return karo
    return credentials