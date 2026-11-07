from fastapi   import Depends , APIRouter,Request
from db.connection import get_db
from depends.is_google_aut import get_gmail_credentials
from  contoler.chat import chat_controller as chat
from pydantic_model.chat import Query
chat_route = APIRouter(
    prefix="/chat"
)


@chat_route.post("/chat")
async def chat_controller(query:Query,credentials = Depends(get_gmail_credentials)):
    return await chat(query,credentials) 