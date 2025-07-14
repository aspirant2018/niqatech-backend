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
    name: str
    wilaya: str
    school: str
    subject: str
    level: str
    subject: str