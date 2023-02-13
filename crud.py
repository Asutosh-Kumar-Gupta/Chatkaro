from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import model
import schema
import config
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_admin_user(db: Session) -> None:
    admin_user = db.query(model.User).filter(model.User.email == "admin@gmail.com").first()
    if not admin_user:
        user_in = schema.UserUpdate(
            username="admin",
            full_name="admin",
            email="admin@gmail.com",
            password=pwd_context.hash("admin"),
            is_admin=True,
            is_active=True
        )
        admin_user = model.User(**user_in.dict())
        db.add(admin_user)
        db.commit()


def get_current_user(db: Session, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = schema.TokenData(username=username, is_admin=payload.get('is_admin'))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = get_user_by_username(db, token_data.username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not pwd_context.verify(password, user.password):
        return False
    return user


def get_user_by_username(db: Session, username: str):
    return db.query(model.User).filter(model.User.username == username).first()


def create_user(db: Session, user: schema.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = model.User(username=user.username, password=hashed_password, full_name=user.full_name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: schema.UserUpdate):
    db_user = db.query(model.User).filter(model.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = user.dict(exclude_unset=True)
    if update_data["password"]:
        hashed_password = pwd_context.hash(update_data["password"])
        del update_data["password"]
        update_data["password"] = hashed_password
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_group(db: Session, group: schema.GroupCreate, user: schema.User):
    db_group = model.Group(name=group.name, description=group.description, owner_id=user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    add_member_to_group(db, db_group, user)
    return db_group


def update_group(db: Session, group_id: int, group: schema.GroupUpdate):
    db_group = db.query(model.Group).filter(model.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    update_data = group.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_group, key, value)
    db.commit()
    db.refresh(db_group)
    return db_group


def get_group(db: Session, group_id: int):
    return db.query(model.Group).filter(model.Group.id == group_id).first()


def delete_group(db: Session, group_id: int):
    db_group = db.query(model.Group).filter(model.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()


def get_user(db: Session, user_id: int):
    return db.query(model.User).filter(model.User.id == user_id).first()


def add_member_to_group(db, group, user):
    db_group = model.GroupMember(group_id=group.id, user_id=user.id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


def remove_member_from_group(db, group, user):
    db_group = db.query(model.GroupMember).filter(model.GroupMember.group_id == group.id,
                                                  model.GroupMember.user_id == user.id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="User not found in group")
    db.delete(db_group)
    db.commit()
    return db_group


def is_member_of_group(db, group, user):
    return db.query(model.GroupMember).filter(model.GroupMember.group_id == group.id,
                                              model.GroupMember.user_id == user.id).first()


def create_group_message(db: Session, message: schema.MessageCreate, group_id: int, user: model.User):
    db_message = model.Message(message=message.message, group_id=group_id, user_id=user.id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_group_message(db, message_id):
    return db.query(model.Message).filter(model.Message.id == message_id).first()


def like_group_message(db: Session, message_id: int, user: model.User):
    db_group = db.query(model.MessageLike).filter(model.MessageLike.message_id == message_id,
                                                  model.MessageLike.user_id == user.id).first()
    if db_group:
        raise HTTPException(status_code=404, detail="You already liked this message")
    db_message = model.MessageLike(message_id=message_id, user_id=user.id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def search_groups(db: Session, name: str):
    return db.query(model.Group).filter(model.Group.name.contains(name)).all()
