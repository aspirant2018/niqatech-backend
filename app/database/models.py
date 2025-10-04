'''
Usually refer to data structures that represent database tables or entities.
In ORMs (like SQLAlchemy, Django ORM), models define the shape of your database records — their fields, types, relations.
Models are tied to persistence, meaning they map to how data is stored and retrieved.
Example: A User model with fields like id, email, hashed_password, stored in a database.
'''


from sqlalchemy import Column, Integer, String, Boolean, Enum, Float, ForeignKey, UniqueConstraint, CheckConstraint, DateTime, func
from sqlalchemy.orm import relationship
from app.v1.schemas.schemas import AcademicLevelEnum
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base
import os




class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)  

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    school_name = Column(String, nullable=True)
    academic_level = Column(Enum(AcademicLevelEnum), nullable=True)
    city = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    file = relationship("UploadedFile", back_populates="user", uselist=False) # Uselist => Ensures it's a one-to-one relationship, Back populate => biderectional
    created_at = Column(DateTime(timezone=True),server_default=func.now(), nullable=False)
    def __repr__(self):
        return f"<teacher(id={self.id}, email={self.email}, first_name={self.first_name}, last_name={self.last_name})>"


UPLOAD_DIR = "app/uploads"

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    file_id      = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, nullable=False)
    user_id      = Column(String, ForeignKey(User.id, ondelete="CASCADE"), unique=True, nullable=False)
    file_name    = Column(String, nullable=False)
    storage_path = Column(String, nullable=False) 
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="file")

    classrooms = relationship(
        "Classroom",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    def generate_storage_path(self) -> str:
        """Generate a  safe path uploads/unique_file_id_filename.ext"""
        _, ext = os.path.splitext(self.file_name)
        return os.path.join(UPLOAD_DIR, self.user_id, f"file_{self.user_id}{ext}")
    
    def __repr__(self):
        return f"<file(file_id={self.file_id}>, file_name={self.file_name}), storage_path={self.storage_path})>, created_at={self.created_at}, updated_at={self.updated_at})"


#  WHAT I WANT TO ADD ARE THE FOLLOWING FIELDS

        # "school_name": "متوسطة مرزقان محمد المدعو معمر (قصر الصباحي)",
        # "term": "الأول",
        # "year": "2020-2021",
        # "level": "أولى  متوسط    1",
        # "subject": "المعلوماتية",
        # "classroom_name": "Sheet-0",
        # "sheet_name": "2100001_1",

class Classroom(Base):
    __tablename__ = "classrooms"

    classroom_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(UUID(as_uuid=True), ForeignKey(UploadedFile.file_id, ondelete="CASCADE"), nullable=False)
    school_name = Column(String, nullable=False)
    term = Column(String, nullable=False)
    year = Column(String, nullable=False)
    level = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    classroom_name = Column(String, nullable=False) 
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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String)
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

    
    __table_args__ = (
        CheckConstraint("evaluation >= 0 AND evaluation <= 20", name="Check_Evaluation_range_eval"),
        CheckConstraint("first_assignment >= 0 AND first_assignment <= 20", name="Check_Evaluation_range_first"),
        CheckConstraint("final_exam >= 0 AND final_exam <= 20", name="Check_Evaluation_range_final"),
    )
    def __repr__(self):
        return f"<student(student_id={self.student_id}>, evaluation={self.evaluation}, first_assignment={self.first_assignment}, final_exam={self.final_exam})"








