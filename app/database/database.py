'''
defines engine, session, Base
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
         
#DATABASE_URL = "sqlite:///./niqatech.db"
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# PostgreSQL
# engine = create_engine("postgresql://postgres:Rahimmazouz707@db:5432/niqatechdb")
engine = create_engine("postgresql://postgres:Rahimmazouz707@localhost:5432/niqatechdb")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


