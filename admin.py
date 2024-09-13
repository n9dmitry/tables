from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.templating import Jinja2Templates
from models import User, SessionLocal, Role  # Не забудьте импортировать Role

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users})

@router.post("/create/")
async def create_user(
    request: Request,
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    login: str = Form(...),
    role: Role = Form(...),  # Добавлено поле для роли
    db: Session = Depends(get_db)
):
    user = User(name=name, surname=surname, email=email, password=password, login=login, role=role)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    return RedirectResponse(url="/admin/", status_code=303)

@router.post("/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return RedirectResponse(url="/admin/", status_code=303)
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/edit/{user_id}")
async def edit_user(
    user_id: int,
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    login: str = Form(...),
    role: Role = Form(...),  # Добавлено поле для роли
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name
    user.surname = surname
    user.email = email
    user.password = password
    user.login = login
    user.role = role  # Обновляем роль
    db.commit()
    return RedirectResponse(url="/admin/", status_code=303)
