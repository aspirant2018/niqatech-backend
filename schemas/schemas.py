from pydantic import BaseModel



class TokenData(BaseModel):
    token: str


class ProfileData(BaseModel):
    name: str
    wilaya: str
    school: str
    subject: str
    level: str
    subject: str