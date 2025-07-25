'''
Usually refer to data structures that represent database tables or entities.

In ORMs (like SQLAlchemy, Django ORM), models define the shape of your database records — their fields, types, relations.

Models are tied to persistence, meaning they map to how data is stored and retrieved.

Example: A User model with fields like id, email, hashed_password, stored in a database.
'''


from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from schemas.schemas import AcademicLevelEnum
import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from database.database import Base





class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    school_name = Column(String, nullable=False)
    academic_level = Column(Enum(AcademicLevelEnum), nullable=False)
    city = Column(String, nullable=False)
    subject = Column(String, nullable=False)

    file = relationship("UploadedFile", back_populates="user", uselist=False) # Uselist => Ensures it's a one-to-one relationship, Back populate => biderectional


    def __repr__(self):
        return f"<teacher(id={self.id}, email={self.email}, first_name={self.first_name}, last_name={self.last_name})>"

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    file_id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, nullable=False)
    user_id = Column(String, ForeignKey(User.id), unique=True, nullable=False)
    file_name = Column(String, nullable=False)
    user = relationship("User", back_populates="file")


    def __repr__(self):
        return f"<file(file_id={self.file_id}, user_id={self.user_id}, file_name={self.file_name})>"



class Classroom(Base):
    __tablename__ = "classrooms"

    classroom_id = Column(Integer, primary_key=True,index=True) 
    file_id = Column(UUID(as_uuid=True), ForeignKey(UploadedFile.file_id, ondelete="CASCADE"), nullable=False)
    classroom_name = Column(String, nullable=False)
    number_of_students = Column(Integer,nullable=False)

    __table_args__ = (
        UniqueConstraint("file_id","classroom_name",name="uix_file_classroom"),
    )

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True)
    row = Column(Integer, nullable=False)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)

    evaluation = Column(Float)
    first_assignment = Column(String)
    final_exam = Column(String)
    observation = Column(String)







