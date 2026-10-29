from pydantic import BaseModel



class Signup(BaseModel):
    name : str
    password :str