'''
defines engine, session, Base
'''
from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import enum

        
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
    #role = Column(Enum(Role), nullable=False)  # Added role field
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    school_name = Column(String, nullable=False)
    academic_level = Column(Enum(AcademicLevelEnum), nullable=False)
    city = Column(String, nullable=False)
    subject = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, first_name={self.first_name}, last_name={self.last_name})>"

class student(Base):
    __tablename__ = 'students'

    student_id = Column(String, primary_key=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    evaluation = Column(Float, nullable=False)
    assignment = Column(Float, nullable=False)
    final = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    classroom_id = Column(Integer, nullable=False, foreign_key=True)

    def __repr__(self):
        return f"<Student(student_id={self.student_id}, is_active={self.is_active})>"
    

    
Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
