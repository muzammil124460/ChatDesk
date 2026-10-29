from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from dotenv import load_dotenv
import os
load_dotenv()




engine = create_engine(os.getenv("DATABASE_URL"))

# 4. Base: database models ka parent
class Base(DeclarativeBase):
    pass


LocalSession = sessionmaker(
    bind=engine,
    
)

def get_db():

    db = LocalSession()

    try:

        yield db 
    finally:
        db.close()


