'''
Usually refer to data structures that represent database tables or entities.
In ORMs (like SQLAlchemy, Django ORM), models define the shape of your database records — their fields, types, relations.
Models are tied to persistence, meaning they map to how data is stored and retrieved.
Example: A User model with fields like id, email, hashed_password, stored in a database.
'''


from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.v1.schemas.schemas import AcademicLevelEnum
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base





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
    user_id = Column(String, ForeignKey(User.id, ondelete="CASCADE"), unique=True, nullable=False)
    file_name = Column(String, nullable=False)

    user = relationship("User", back_populates="file")

    classrooms = relationship(
        "Classroom",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<file(file_id={self.file_id}>"



class Classroom(Base):
    __tablename__ = "classrooms"

    classroom_id = Column(Integer, primary_key=True,index=True) 
    file_id = Column(UUID(as_uuid=True), ForeignKey(UploadedFile.file_id, ondelete="CASCADE"), nullable=False)
    sheet_name = Column(String, nullable=False)
    number_of_students = Column(Integer,nullable=False)

    students = relationship(
        "Student",
        back_populates="classroom",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    file = relationship("UploadedFile", back_populates="classrooms")

    
    # The UniqueConstraint("file_id", "sheet_name") prevents duplicate classroom records for the same sheet within the same Excel file.
    __table_args__ = (
        UniqueConstraint("file_id","sheet_name",name="uix_file_classroom"),
    )

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True)
    classroom_id = Column(String, ForeignKey(Classroom.classroom_id, ondelete="CASCADE"), nullable=False)
    row = Column(Integer, nullable=False)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    date_birth = Column(String, nullable=False)
    evaluation = Column(Float)
    first_assignment = Column(Float)
    final_exam = Column(Float)
    observation = Column(String)


    classroom = relationship("Classroom", back_populates="students")

    __table_args__=(
        CheckConstraint('evaluation >= 0 AND evaluation <=20',name='Check_Evaluation_range'),
        CheckConstraint('first_assignment >= 0 AND first_assignment <=20',name='Check_Evaluation_range'),
        CheckConstraint('final_exam >= 0 AND final_exam <=20',name='Check_Evaluation_range'),
    )

    def __repr__(self):
        return f"<student(student_id={self.student_id}>, evaluation={self.evaluation}"








