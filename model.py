from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from db_handler import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(200))
    full_name = Column(String(60))
    email = Column(String(60))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    groups = relationship("GroupMember", back_populates="user")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    name = Column(String(60), unique=True, index=True)
    description = Column(String(250))
    owner_id = Column(Integer, ForeignKey("users.id"))

    members = relationship("GroupMember", back_populates="group")
    messages = relationship("Message", back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="groups")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String(250))

    group = relationship("Group", back_populates="messages")
    user = relationship("User")
    likes = relationship("MessageLike", back_populates="message")


class MessageLike(Base):
    __tablename__ = "message_likes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    message = relationship("Message", back_populates="likes")
    user = relationship("User")
