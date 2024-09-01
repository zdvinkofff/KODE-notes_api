from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from . import models, schemas, auth
from .database import SessionLocal, engine
from .auth import get_current_user

app = FastAPI()

# Создание таблиц в базе данных
models.Base.metadata.create_all(bind=engine)

# Маршрут для создания пользователя
@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(SessionLocal)):
    db_user = auth.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Маршрут для получения токена
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(SessionLocal)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Маршрут для создания заметки
@app.post("/notes/", response_model=schemas.NoteOut)
def create_note(note: schemas.NoteCreate, db: Session = Depends(SessionLocal), current_user: models.User = Depends(get_current_user)):
    # Проверка орфографии заголовка и содержимого заметки
    title_errors = check_spelling(note.title)
    content_errors = check_spelling(note.content)

    if title_errors or content_errors:
        error_details = {
            "title_errors": title_errors,
            "content_errors": content_errors
        }
        raise HTTPException(status_code=400, detail=f"Spelling errors found: {error_details}")

    db_note = models.Note(**note.dict(), owner_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

# Маршрут для получения списка заметок
@app.get("/notes/", response_model=List[schemas.NoteOut])
def read_notes(skip: int = 0, limit: int = 10, db: Session = Depends(SessionLocal), current_user: models.User = Depends(get_current_user)):
    notes = db.query(models.Note).filter(models.Note.owner_id == current_user.id).offset(skip).limit(limit).all()
    return notes