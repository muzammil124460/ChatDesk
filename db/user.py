from sqlalchemy import Integer,String
from connection import Base
from sqlalchemy.orm import Mapped,mapped_column



class User_table(Base):
    __tablename__ : "User"

    id : Integer = mapped_column(primary_key=True)
    name : String
    password : Integer




