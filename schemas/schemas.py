from pydantic import BaseModel , Field
from typing import List, Optional
import enum


# Enums
class AcademicLevelEnum(enum.Enum):
    primary = "primary"
    secondary = "secondary"
    higher = "higher"

class TokenData(BaseModel):
    token: str


class ProfileData(BaseModel):
    email: str # i must give it the Email type from pydantic
    first_name: str
    last_name: str
    school_name: str
    academic_level: str
    city: str
    subject: str


class ItemResponse(BaseModel):
    message: str
    user_id: str
    email: str
    is_profile_complete: bool
    jwt_token: str




class Student(BaseModel):
    id: int             = Field(description="The student ID")
    row: int            = Field(description="The i-th row of the student in the Excel File")
    last_name: str      = Field(description="Student last name")
    first_name: str     = Field(description="Student first name")
    date_of_birth: str  = Field(description="Student last name")
    evaluation: Optional[float]       = Field(description="The evaluation grade ")
    first_assignment: Optional[float] = Field(description="The first assignment grade")
    final_exam: Optional[float]       = Field(description="The final exam grade")
    observation: Optional[str]        = Field(description="The observation given by the teacher")

class Classroom(BaseModel):
    school_name: str = Field(description="The first assignment grade")
    term: str 
    year: str
    level: str
    subject: str
    classroom_id: str
    classroom_name: str
    number_of_students: int
    students: List[Student]

class WorkbookParseResponse(BaseModel):
    message: str = "XLS file parsed successfully"
    data: dict[str, List[Classroom]]  # {"classrooms": [...]}
