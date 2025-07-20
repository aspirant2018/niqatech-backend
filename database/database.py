'''
defines engine, session, Base
'''
import uuid
from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import enum
from sqlalchemy.dialects.postgresql import UUID


        
# Database URL
DATABASE_URL = "sqlite:///./niqatech.db" 
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class AcademicLevelEnum(enum.Enum):
    primary = "primary"
    secondary = "secondary"
    higher = "higher"

class User(Base):
    __tablename__ = 'users'

    id = Column(String,unique=True, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    school_name = Column(String, nullable=False)
    academic_level = Column(Enum(AcademicLevelEnum), nullable=False)
    city = Column(String, nullable=False)
    subject = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, first_name={self.first_name}, last_name={self.last_name})>"

class UploadedFile(Base):
    __tablename__ = 'files'

    file_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, nullable=False)
    # user_id = Column(String, ForeignKey(User.id), unique=True, nullable=False)
    user_id = Column(String, unique=True, nullable=False)
    file_name = Column(String, nullable=False)


    def __repr__(self):
        return f"<file(file_id={self.file_id}, user_id={self.user_id}, file_name={self.file_name})>"
    

    
Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
