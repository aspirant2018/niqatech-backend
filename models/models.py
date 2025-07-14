'''
Usually refer to data structures that represent database tables or entities.

In ORMs (like SQLAlchemy, Django ORM), models define the shape of your database records — their fields, types, relations.

Models are tied to persistence, meaning they map to how data is stored and retrieved.

Example: A User model with fields like id, email, hashed_password, stored in a database.
'''


from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import declarative_base
from schemas.schemas import AcademicLevelEnum


Base = declarative_base()




class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    school_name = Column(String, nullable=False)
    academic_level = Column(Enum(AcademicLevelEnum), nullable=False)
    city = Column(String, nullable=False)
    subject = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, first_name={self.first_name}, last_name={self.last_name})>"
    
