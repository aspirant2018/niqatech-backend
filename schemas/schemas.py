from pydantic import BaseModel
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
    email: str
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
    id: int
    row: int
    last_name: str
    first_name: str
    date_of_birth: str  # or date if you parse it
    evaluation: Optional[float]
    first_assignment: Optional[float]
    final_exam: Optional[float]
    observation: Optional[str]

class Classroom(BaseModel):
    school_name: str
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
