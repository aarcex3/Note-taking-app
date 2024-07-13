from pydantic import BaseModel, EmailStr
from pydantic.types import SecretStr


class UserSchema(BaseModel):
  username: str
  email: EmailStr
  password: SecretStr


class RegisterUserSchema(BaseModel):
  username: str
  email: EmailStr
  password: SecretStr


class LoginUserSchema(BaseModel):
  username: str
  password: SecretStr
