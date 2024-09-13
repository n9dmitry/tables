from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from models import SessionLocal, create_superuser, User
from admin import router as admin_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Проверка и создание суперпользователя при старте приложения
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    create_superuser(db)
    db.close()


# Отображение страницы авторизации
@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Авторизация пользователя
@app.post("/login/")
def login(request: Request, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == login).first()
    if user is None or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return templates.TemplateResponse("index.html", {"request": request, "user": user.name})


# Разные страницы для каждого пункта меню
@app.get("/manager", response_class=HTMLResponse)
def manager_page(request: Request):
    return templates.TemplateResponse("manager.html", {"request": request})



@app.get("/printer", response_class=HTMLResponse)
def printer_page(request: Request):
    return templates.TemplateResponse("printer.html", {"request": request})


@app.get("/results", response_class=HTMLResponse)
def results_page(request: Request):
    return templates.TemplateResponse("results.html", {"request": request})



app.include_router(admin_router, prefix="/admin")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
