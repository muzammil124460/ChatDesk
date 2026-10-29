from fastapi import FastAPI
from db.connection import engine, Base
from starlette.middleware.sessions import SessionMiddleware
import os
from routes.auth import auth
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


# connection of db
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")



# middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("MIDD_SECRETE"),
     same_site="lax",
    https_only=False,  


)


app.include_router(auth)

@app.get("/")
def test():
    return "server is started"