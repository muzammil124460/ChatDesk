from fastapi import Request,HTTPException,Depends
import os
from db.user import User
from sqlalchemy.orm import Session

from fastapi import Request
import os
import jwt
from db.connection import get_db

async def is_authenticated(request: Request, db:Session=Depends(get_db)):
   
    token = request.headers.get("authorization").split(" ")[-1]
    if not token:
        raise HTTPException(
            status_code=401,
            detail=" token not found "
        )


    decoded_token = jwt.decode(token,os.getenv("SECRET_KEY"),algorithms=os.getenv("ALGORITHM"))
    print("token:",decoded_token)

    id = decoded_token.get("id")
    if not id:
        raise HTTPException(
            status_code=401,
            detail="user id not found"
        )

    try:
        user =  db.query(User).filter(User.id == id).first()

        if not user:
            raise HTTPException(
                status_code=402,
                detail="User not found in database"
            )

        return {"id":user.id,"email":user.email}

    
    except Exception as err:

        raise HTTPException(
            status_code=500,
            detail="User is not authorized "
        ) from err



    
