from pydantic import BaseModel, EmailStr, Field


class UserRequest(BaseModel):
    username: EmailStr = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=8)


class Response(BaseModel):
    id: int = Field(default=1, ge=1)
    email: EmailStr

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
