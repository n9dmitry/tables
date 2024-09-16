from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from models import Order, SessionLocal, User

router = APIRouter()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Зависимость для получения текущего пользователя (вы можете адаптировать этот код под ваши нужды)
def get_current_active_user(token: str = Depends(authenticate_user)):
    # Тут ваша логика аутентификации
    user = ...  # Получите пользователя на основе токена
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Проверка роли пользователя
def check_user_role(user: User):
    if user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

# Создание заказа
@router.post("/orders/")
def create_order(
    request: Request,
    task_number: str = Form(...),
    date: str = Form(...),
    plot: str = Form(...),
    material: str = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    eyelets: str = Form(...),
    spike: str = Form(...),
    reinforcement: str = Form(...),
    quantity: int = Form(...),
    customer: str = Form(...),
    price_per_unit: float = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    check_user_role(user)  # Проверяем роль пользователя
    total_amount = price_per_unit * quantity
    new_order = Order(
        task_number=task_number,
        date=date,
        plot=plot,
        material=material,
        width=width,
        height=height,
        eyelets=eyelets,
        spike=spike,
        reinforcement=reinforcement,
        quantity=quantity,
        customer=customer,
        price_per_unit=price_per_unit,
        total_amount=total_amount
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {"message": "Order created successfully", "order": new_order}

# Редактирование заказа
@router.put("/orders/{order_id}")
def update_order(
    order_id: int,
    request: Request,
    task_number: str = Form(...),
    date: str = Form(...),
    plot: str = Form(...),
    material: str = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    eyelets: str = Form(...),
    spike: str = Form(...),
    reinforcement: str = Form(...),
    quantity: int = Form(...),
    customer: str = Form(...),
    price_per_unit: float = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)  # Получаем текущего пользователя
):
    check_user_role(user)  # Проверяем роль пользователя

    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    order.task_number = task_number
    order.date = date
    order.plot = plot
    order.material = material
    order.width = width
    order.height = height
    order.eyelets = eyelets
    order.spike = spike
    order.reinforcement = reinforcement
    order.quantity = quantity
    order.customer = customer
    order.price_per_unit = price_per_unit
    order.total_amount = price_per_unit * quantity

    db.commit()
    db.refresh(order)

    return {"message": "Order updated successfully", "order": order}

# Получение всех заказов
@router.get("/orders/")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return {"orders": orders}

# Получение конкретного заказа
@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order": order}
