from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from models import SessionLocal, create_superuser, User, Role
from admin import router as admin_router
from contextlib import asynccontextmanager

templates = Jinja2Templates(directory="templates")

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Проверка и создание суперпользователя при старте приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        create_superuser(db)
        yield
    finally:
        db.close()

app = FastAPI(lifespan=lifespan)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Проверка сессии пользователя
def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == int(session_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Отображение страницы авторизации
@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Авторизация пользователя
@app.post("/login/")
def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.login == login).first()
    if user is None or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    response = templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "role": user.role.value,
        "name": user.name.value,
    })
    response.set_cookie(key="session_id", value=user.id)
    return response

@app.get("/", response_class=RedirectResponse)
def redirect_to_login():
    return RedirectResponse(url="/login")

# Функция для выхода из системы
@app.post("/logout")
def logout(response: RedirectResponse):
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_id")  # Удаление куки
    return response

# Разные страницы для каждого пункта меню
def check_role_access(user: User, allowed_roles: set):
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

@app.get("/manager", response_class=HTMLResponse)
def manager_page(request: Request, current_user: User = Depends(get_current_user)):
    check_role_access(current_user, {Role.manager, Role.superuser, Role.admin})
    return templates.TemplateResponse("manager.html", {
        "request": request,
        "user": current_user,
        "role": current_user.role.value,
    })

@app.get("/printer", response_class=HTMLResponse)
def printer_page(request: Request, current_user: User = Depends(get_current_user)):
    check_role_access(current_user, {Role.printer, Role.superuser, Role.admin})
    return templates.TemplateResponse("printer.html", {
        "request": request,
        "user": current_user,
        "role": current_user.role.value,
    })

@app.get("/results", response_class=HTMLResponse)
def results_page(request: Request, current_user: User = Depends(get_current_user)):
    check_role_access(current_user, {Role.superuser, Role.admin})
    return templates.TemplateResponse("results.html", {
        "request": request,
        "user": current_user,
        "role": current_user.role.value,
    })


app.include_router(admin_router, prefix="/admin", dependencies=[Depends(get_current_user)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
