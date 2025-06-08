from typing import Literal
from pydantic import BaseModel, EmailStr

class UserIn(BaseModel):
    first_name: str
    last_name:  str
    email:      EmailStr
    age:        int
    gender:     Literal["Male", "Female"]
    # роль не приходит от клиента, мы её сами подставляем в коде при регистрации:
    # role: Literal["user", "admin"] = "user"

class UserOut(UserIn):
    id:   str
    role: Literal["user", "admin"]
