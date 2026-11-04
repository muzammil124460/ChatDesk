from pydantic import BaseModel



class Signup(BaseModel):
    email:str
    name : str
    password :str
    create_at : str


class token(BaseModel):
    email:str
    name:str
