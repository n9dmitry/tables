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

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == int(session_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def check_admin_access(user: User):
    if user.role not in (Role.superuser, Role.admin):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

@router.get("/", response_class=HTMLResponse)
async def admin_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin_access(current_user)  # Проверяем доступ
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
    role: Role = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_access(current_user)  # Проверяем доступ
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
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin_access(current_user)  # Проверяем доступ
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
    role: Role = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_access(current_user)  # Проверяем доступ
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name
    user.surname = surname
    user.email = email
    user.password = password
    user.login = login
    user.role = role
    db.commit()
    return RedirectResponse(url="/admin/", status_code=303)
