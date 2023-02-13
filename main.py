from datetime import timedelta
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import crud
import model
import schema
import config
import utils
from db_handler import SessionLocal, engine

model.Base.metadata.create_all(bind=engine)

# initiating app
app = FastAPI(
    title="ChatKaro",
    description="A chatting app where people can chat in any group",
    version="1.0.0"
)
model.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


crud.create_admin_user(db=SessionLocal())

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/token/", response_model=schema.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(data={"sub": user.username, "is_admin": user.is_admin},
                                             expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schema.User)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="You dont have admin role")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.put("/users/{user_id}", response_model=schema.User)
def update_user(user_id: int, user: schema.UserUpdate, db: Session = Depends(get_db),
                token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="You dont have admin role")
    return crud.update_user(db=db, user_id=user_id, user=user)


@app.post("/groups/", response_model=schema.Group)
def create_group(group: schema.GroupCreate, db: Session = Depends(get_db),
                 token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    return crud.create_group(db=db, group=group, user=current_user)


@app.put("/groups/{group_id}", response_model=schema.Group)
def update_group(group_id: int, group: schema.GroupUpdate, db: Session = Depends(get_db),
                 token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    return crud.update_group(db=db, group_id=group_id, group=group)


@app.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db),
                 token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    group = crud.get_group(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    print(group)
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this group")
    crud.delete_group(db, group_id=group_id)
    return {"message": "Group deleted"}


@app.get("/groups/search")
async def search_group(name: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    groups = crud.search_groups(db, name)
    return {"groups": [{"id": group.id, "name": group.name, "description": group.description} for group in groups]}


@app.post("/groups/{group_id}/members/", response_model=schema.GroupMember)
def add_member_to_group(group_id: int, user_id: int, db: Session = Depends(get_db),
                        token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    group = crud.get_group(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this group")
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.add_member_to_group(db=db, group=group, user=user)


@app.delete("/groups/{group_id}/members/{user_id}", response_model=schema.GroupMember)
def remove_member_from_group(group_id: int, user_id: int, db: Session = Depends(get_db),
                             token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    group = crud.get_group(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this group")
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.remove_member_from_group(db=db, group=group, user=user)


# Group Messages
@app.post("/groups/{group_id}/messages/", response_model=schema.GroupMessage)
def create_group_message(group_id: int, message: schema.MessageCreate, db: Session = Depends(get_db),
                         token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    group = crud.get_group(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not crud.is_member_of_group(db, group=group, user=current_user):
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    return crud.create_group_message(db=db, message=message, group_id=group_id, user=current_user)


@app.post("/groups/{group_id}/messages/{message_id}/likes/", response_model=schema.MessageLike)
def like_group_message(group_id: int, message_id: int, db: Session = Depends(get_db),
                       token: str = Depends(oauth2_scheme)):
    current_user = crud.get_current_user(db, token=token)
    group = crud.get_group(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if not crud.is_member_of_group(db, group=group, user=current_user):
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    message = crud.get_group_message(db, message_id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return crud.like_group_message(db=db, message_id=message_id, user=current_user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
