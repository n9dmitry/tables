from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import SessionLocal, create_superuser, User, Order
from admin import router as admin_router
from contextlib import asynccontextmanager
from datetime import datetime


templates = Jinja2Templates(directory="templates")

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        create_superuser(db)
        yield
    finally:
        db.close()

app = FastAPI(lifespan=lifespan)


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
def login(request: Request, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == login).first()
    if user is None or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    response = templates.TemplateResponse("index.html", {"request": request, "user": user})
    response.set_cookie(key="session_id", value=user.id)  # Пример установки сессии
    return response

# Перенаправление с главной страницы на страницу авторизации
@app.get("/", response_class=RedirectResponse)
def redirect_to_login():
    return RedirectResponse(url="/login")




@app.get("/printer", response_class=HTMLResponse)
async def printer_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).order_by(Order.id.desc()).all()

    return templates.TemplateResponse("printer.html",
                                      {"request": request, "orders": orders, "current_user": current_user})

# Разные страницы для каждого пункта меню
@app.get("/manager", response_class=HTMLResponse)
def manager_page(request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
                 ):
    orders = db.query(Order).order_by(Order.id.desc()).all()

    return templates.TemplateResponse("manager.html",
                                      {"request": request, "orders": orders, })


@app.get("/results", response_class=HTMLResponse)
def results_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("results.html", {"request": request})


@app.post("/orders")
async def create_order(
        task_number: int = Form(...),
        date: str = Form(...),  # Дата как строка
        subject: str = Form(...),
        material: str = Form(...),
        quantity: int = Form(...),
        performer: str = Form(...),
        print_width: float = Form(...),
        print_height: float = Form(...),
        canvas_width: float = Form(...),
        canvas_length: float = Form(...),
        eyelets: str = Form(...),
        spike: str = Form(...),
        reinforcement: str = Form(...),
        db: Session = Depends(get_db)  # Предполагается, что get_db определен
):
    # Преобразуем строку даты в объект datetime.date
    date_object = datetime.strptime(date, '%Y-%m-%d').date()

    # Создаем новый заказ
    new_order = Order(
        task_number=task_number,
        date=date_object,
        subject=subject,
        material=material,
        quantity=quantity,
        performer=performer,
        print_width=print_width,
        print_height=print_height,
        canvas_width=canvas_width,
        canvas_length=canvas_length,
        eyelets=eyelets,
        spike=spike,
        reinforcement=reinforcement,
    )

    # Добавляем и коммитим заказ в БД
    db.add(new_order)
    db.commit()

    return {"message": "Order created successfully", "order_id": new_order.id}


@app.post("/orders/{order_id}/update")
async def update_order(order_id: int,
                       customer: str = Form(...),
                       price_per_unit: int = Form(...),
                       total_amount: int = Form(...),
                       db: Session = Depends(get_db)):
    # Получаем заказ из БД
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Обновляем данные заказа
    order.customer = customer
    order.price_per_unit = price_per_unit
    order.total_amount = total_amount

    # Сохраняем изменения
    db.commit()
    db.refresh(order)

    return {"message": "Order updated successfully", "order": order}


app.include_router(admin_router, prefix="/admin", dependencies=[Depends(get_current_user)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
