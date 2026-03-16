from pydantic import BaseModel, EmailStr, Field


class SignupForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class GenerateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class GenerateResponse(BaseModel):
    outputs: dict[str, str]
    remaining: int
