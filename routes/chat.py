from fastapi   import Depends , APIRouter
from db.connection import get_db
from depends.is_google_aut import get_gmail_credentials
from agents.mail.crud import chat_controller

chat_route = APIRouter(
    prefix="/chat"
)


@chat_route.get("/start")
def chat(user = Depends(get_gmail_credentials)):
    return chat_controller(user) 