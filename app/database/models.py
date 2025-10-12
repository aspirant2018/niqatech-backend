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
    
    # Primary identifiers
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)

    # Authentication
    hash_password = Column(String, nullable=True)  
    auth_provider = Column(String, nullable=False)  # e.g., 'google', 'facebook', 'local'
    is_active = Column(Boolean, default=True, nullable=False)
    profile_complete = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Profile information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    school_name = Column(String, nullable=True)
    academic_level = Column(Enum(AcademicLevelEnum), nullable=True)
    
    city = Column(String, nullable=True) # City would be replaced by the following three fields
    #wilaya = Column(String, nullable=True)
    #daira = Column(String, nullable=True)
    #commune = Column(String, nullable=True)

    subject = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True),server_default=func.now(), nullable=False)
    
    # Relationships
    file = relationship("UploadedFile",
                        back_populates="user", 
                        uselist=False
                        ) # Uselist => Ensures it's a one-to-one relationship, Back populate => biderectional
    
    def __repr__(self):
        return (
            f"<User(id={self.id}, email={self.email}, "
            f"name={self.first_name} {self.last_name}, "
            f"provider={self.auth_provider})>"
        )
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or "Unknown User"

    @property
    def is_profile_complete(self)-> bool:
        required_fields = [
            self.first_name,
            self.last_name,
            self.school_name,
            self.academic_level,
            self.city,
            self.subject
        ]
        return all(required_fields)
    @property
    def to_dict(self)-> dict:
        """Return a dictionary representation of the user, excluding sensitive info."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "school_name": self.school_name,
            "academic_level": self.academic_level.value if self.academic_level else None,
            "city": self.city,
            "subject": self.subject,
            "auth_provider": self.auth_provider,
            "is_profile_complete": self.is_profile_complete,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
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








