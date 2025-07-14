from pydantic import BaseModel
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

