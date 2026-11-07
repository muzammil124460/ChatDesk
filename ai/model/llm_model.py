from langchain_groq import ChatGroq
import os 
from dotenv import load_dotenv

load_dotenv()


model = ChatGroq(model="openai/gpt-oss-120b",api_key=os.getenv("MODEL_API_KEY"))