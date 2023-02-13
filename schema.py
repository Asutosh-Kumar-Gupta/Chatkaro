from typing import Optional, List
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    full_name: str = None
    email: str = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str = None
    is_active: bool = True
    is_admin: bool = False


class UserInDB(UserUpdate):
    id: int


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        orm_mode = True


class GroupBase(BaseModel):
    name: str
    description: str = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(GroupBase):
    pass


class Group(GroupBase):
    id: int

    # members: List[User] = []

    class Config:
        orm_mode = True


class GroupMemberBase(BaseModel):
    user_id: int


class GroupMemberCreate(GroupMemberBase):
    pass


class GroupMember(GroupMemberBase):
    id: int
    group_id: int
    user: User

    class Config:
        orm_mode = True


class MessageBase(BaseModel):
    message: str


class MessageCreate(MessageBase):
    pass


class GroupMessage(MessageBase):
    id: int
    group_id: int
    user_id: int

    class Config:
        orm_mode = True


class Message(MessageBase):
    id: int
    group_id: int
    user_id: int
    likes: List["MessageLike"] = []

    class Config:
        orm_mode = True


class MessageLike(BaseModel):
    id: int
    user_id: int
    message_id: int

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    is_admin: bool
