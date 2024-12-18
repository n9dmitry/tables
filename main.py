from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import SessionLocal, create_superuser, User, Order, Result, Role, Settings, LoginForm
from admin import router as admin_router
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from datetime import date
#

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


# def check_admin_access(user: User):
#     if user.role not in (Role.superuser, Role.admin):
#         raise HTTPException(status_code=403, detail="Доступ запрещен")

@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login/")
async def login(
    request: Request,
    db: Session = Depends(get_db),
    login: str = Form(...),  # Изменено на Form для получения данных из формы
    password: str = Form(...),  # Изменено на Form для получения данных из формы
):
    # Создаём объект Pydantic для валидации
    login_data = LoginForm(login=login, password=password)

    # Поиск пользователя по логину
    user = db.query(User).filter(User.login == login_data.login).first()

    if user is None or user.password != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Ответ с установкой куки
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "role": user.role,
        "name": user.name,
    })
    response.set_cookie(key="session_id", value=user.id)
    return response


@app.get("/", response_class=RedirectResponse)
def redirect_to_login():
    return RedirectResponse(url="/login")


@app.post("/logout")
def logout(response: RedirectResponse):
    response.delete_cookie("session_id")  # Удаление куки
    return RedirectResponse(url="/login", status_code=302)


# Разные страницы для каждого пункта меню
def check_role_access(user: User, allowed_roles: set):
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")


@app.get("/printer", response_class=HTMLResponse)
async def printer_page(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    check_role_access(current_user, {Role.printer, Role.superuser, Role.admin})
    orders = db.query(Order).order_by(Order.id.desc()).all()

    return templates.TemplateResponse("printer.html",
                                      {"request": request,
                                       "orders": orders,
                                       "current_user": current_user,
                                       "role": current_user.role.value, })


@app.get("/manager", response_class=HTMLResponse)
def manager_page(request: Request,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)
                 ):
    check_role_access(current_user, {Role.manager, Role.superuser, Role.admin})
    orders = db.query(Order).order_by(Order.id.desc()).all()

    return templates.TemplateResponse("manager.html",
                                      {"request": request,
                                       "user": current_user,
                                       "role": current_user.role.value,
                                       "orders": orders, }
                                      )


@app.get("/results", response_class=HTMLResponse)
def results_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_role_access(current_user, {Role.superuser, Role.admin})

    # orders = db.query(Order).order_by(Order.id.desc()).all()
    results = db.query(Result).order_by(Result.order_id.desc()).all()
    return templates.TemplateResponse("results.html", {"request": request,
                                                       "results": results,
                                                       "user": current_user,
                                                       "role": current_user.role.value, })


@app.get("/summary", response_class=HTMLResponse)
def summary_page(
        request: Request,
        db: Session = Depends(get_db),  # Подключение к БД
        current_user: User = Depends(get_current_user)  # Получаем текущего пользователя
):
    # Проверка прав доступа пользователя
    check_role_access(current_user, {Role.superuser, Role.admin})

    # Получаем все заказы текущего пользователя (или все заказы, если для админов)
    if current_user.role in {Role.superuser, Role.admin}:
        orders = db.query(Order).order_by(Order.id.desc()).all()
    else:
        orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.id.desc()).all()

    # Получаем все результаты (если нужно)
    results = db.query(Result).order_by(Result.order_id.desc()).all()
    settings = db.query(Settings).order_by(Settings.id.desc()).all()

    actual_settings = settings[0] if settings else None
    # Получение настроек (если нужно)
    settings_el = (
        db.query(Settings)
        .filter(Settings.updated_at <= datetime.utcnow())
        .order_by(Settings.updated_at.desc())
        .first()
    )

    # Рендеринг шаблона
    return templates.TemplateResponse("summary.html", {
        "request": request,
        "results": results,
        "orders": orders,
        "user": current_user,
        "role": current_user.role.value,
        "settings": settings_el,
        "actual_settings": actual_settings
    })


@app.post("/orders")
async def create_order(
        request: Request,
        current_user: User = Depends(get_current_user),
        task_number: int = Form(...),
        date: str = Form(...),
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
        db: Session = Depends(get_db),
):
    check_role_access(current_user, {Role.printer, Role.superuser, Role.admin})

    date_object = datetime.strptime(date, '%Y-%m-%d').date()
    existing_order = db.query(Order).filter(Order.task_number == task_number).first()

    if existing_order:
        message = "Заказ с этим номером задачи уже существует."
        message_type = "danger"
    else:
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

        new_result = Result(order=new_order)
        db.add(new_order)
        db.add(new_result)
        db.commit()

        message = "Заказ успешно создан!"
        message_type = "success"

    # Показать шаблон с сообщением
    orders = db.query(Order).order_by(Order.id.desc()).all()
    return templates.TemplateResponse("printer.html", {
        "request": request,
        "orders": orders,
        "message": message,
        "message_type": message_type,
        "user": current_user,
        "role": current_user.role.value,
    })


@app.post("/printer/{order_id}")
async def update_orders(
        order_id: int,
        request: Request,
        current_user: User = Depends(get_current_user),
        task_number: int = Form(...),
        date: str = Form(...),
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
        db: Session = Depends(get_db),
):
    check_role_access(current_user, {Role.printer, Role.superuser, Role.admin})

    date_object = datetime.strptime(date, '%Y-%m-%d').date()
    existing_order = db.query(Order).filter(Order.id == order_id).first()

    if not existing_order:
        message = "Заказ не найден."
        message_type = "danger"
    else:
        existing_order.task_number = task_number
        existing_order.date = date_object
        existing_order.subject = subject
        existing_order.material = material
        existing_order.quantity = quantity
        existing_order.performer = performer
        existing_order.print_width = print_width
        existing_order.print_height = print_height
        existing_order.canvas_width = canvas_width
        existing_order.canvas_length = canvas_length
        existing_order.eyelets = eyelets
        existing_order.spike = spike
        existing_order.reinforcement = reinforcement

        db.commit()

        message = "Заказ успешно обновлён!"
        message_type = "success"

    # Показать шаблон с сообщением
    orders = db.query(Order).order_by(Order.id.desc()).all()
    return templates.TemplateResponse("printer.html", {
        "request": request,
        "orders": orders,
        "message": message,
        "message_type": message_type,
        "user": current_user,
        "role": current_user.role.value,
    })


@app.post("/orders/update")
async def update_order(
        request: Request,
        current_user: User = Depends(get_current_user),
        order_id: int = Form(...),
        customer: str = Form(...),
        price_per_unit: int = Form(...),
        db: Session = Depends(get_db)
):
    check_role_access(current_user, {Role.manager, Role.superuser, Role.admin})
    # Получаем заказ из БД
    order = db.query(Order).filter(Order.id == order_id).first()
    # last_setting = db.query(Settings).order_by(Settings.id.desc()).first()
    # if last_setting is not None:
    #     settings_el = db.query(Settings).filter(Settings.id == last_setting.id - 1).first()
    # else:
    #     settings_el = None
    # print(last_setting.id)
    # print(settings_el)

    # settings = db.query(Settings).order_by(Settings.id.desc()).all()

    if order is not None:
        order_date = order.date

        # Ищем настройки, которые были обновлены до даты заказа
        settings_el = (
            db.query(Settings)
            .filter(Settings.updated_at <= datetime.utcnow())
            .order_by(Settings.updated_at.desc())
            .first()
        )
    else:
        settings_el = None

    if not order:
        message = "Заказ не найден."
        message_type = "danger"
    else:
        # Обновляем данные заказа
        order.customer = customer
        order.price_per_unit = price_per_unit

        # Сохраняем изменения
        db.commit()
        order.total_amount = order.quantity * order.price_per_unit
        db.commit()

        db.refresh(order)

        # Обновляем формулы result
        def round_custom(value):
            return round(value, 2) if value is not False else False

        # Вычисляем общие площади
        order.result.total_print_area = order.print_width * order.print_height * order.quantity
        order.result.total_print_area = round((order.result.total_print_area), 3)
        order.result.total_canvas_area = round_custom(
            order.canvas_width * order.canvas_length * order.quantity)

        # Общее количество красок
        order.result.total_paints = round_custom(
            settings_el.paint_consumption_m2 * order.result.total_print_area
        )
        # Люверсы
        if order.eyelets.lower() == "да":
            order.result.total_eyelets = round_custom(
                ((order.print_width + order.print_height) * 2 / settings_el.eyelet_step + 4) * order.quantity)
        else:
            order.result.total_eyelets = False




        # Шипы
        if order.spike == "да":
            order.result.total_spikes = round_custom(((max(order.print_width,
                                                           order.print_height) / 3 - 1) * min(
                order.print_width, order.print_height)) * order.quantity)
        else:
            order.result.total_spikes = False

        # Укрепления
        if order.reinforcement == "да":
            order.result.total_reinforcements = round_custom(
                (order.print_width + order.print_height) * 2 * 0.1 * order.quantity)
        else:
            order.result.total_reinforcements = False

        # Расходы на.canvas
        canvas_prices = {
            "Блюбэк": settings_el.blueback_price_m2,
            "Баннер литой 450гм": settings_el.banner_molded_price_m2,
            "Баннер ламинат 440гм": settings_el.banner_laminated_price_m2,
            "Сетка": settings_el.mesh_price_m2
        }
        order.result.expenses_canvas = round_custom(
            canvas_prices.get(order.material, False) * order.result.total_canvas_area)

        # Расходы краски и люверсы
        order.result.expenses_prints = round_custom(
            settings_el.paint_price_liter * order.result.total_paints)
        order.result.expenses_eyelets = round_custom(settings_el.eyelet_price * order.result.total_eyelets)

        # Расходы на уСИЛЕНИЯ
        order.result.expenses_reinforcements = round_custom(
            settings_el.banner_molded_price_m2 * order.result.total_reinforcements) if order.reinforcement == "да" else False

        # Заработки
        order.result.salary_printer = round_custom(
            settings_el.printer_rate_m2 * order.result.total_print_area)
        order.result.salary_eyelet_worker = round_custom(
            settings_el.eyelet_rate * order.result.total_eyelets)
        order.result.salary_cutter = round_custom(
            settings_el.cutter_rate_m2 * order.result.total_eyelets) if order.material == "Блюбэк" else False
        order.result.salary_welder = round_custom(
            settings_el.payer_rate * order.result.total_spikes) if order.result.total_eyelets is not False else False

        # Общие расходы
        order.result.total_expenses = sum(filter(None, [
            order.result.expenses_canvas,
            order.result.expenses_prints,
            order.result.expenses_eyelets,
            order.result.expenses_reinforcements,
            order.result.salary_printer,
            order.result.salary_eyelet_worker,
            order.result.salary_cutter,
            order.result.salary_welder
        ]))

        order.result.total_expenses = round_custom(order.result.total_expenses)

        # Налоги и маржа
        order.result.tax = round_custom(0.05 * order.total_amount)
        order.result.margin = round_custom(
            order.total_amount - order.result.tax - order.result.total_expenses)

        # Сохраняем изменения
        db.commit()
        db.refresh(order)

        message = "Заказ обновлён успешно!"
        message_type = "success"

    # Показать шаблон с сообщением
    orders = db.query(Order).order_by(Order.id.desc()).all()
    return templates.TemplateResponse("manager.html", {
        "request": request,
        "orders": orders,
        "message": message,
        "message_type": message_type,
        "user": current_user,
        "role": current_user.role.value,
    })


@app.post("/order/delete/{order_id}")
async def delete_order(
        order_id: int,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    check_role_access(current_user, {Role.superuser, Role.admin})

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        message = "Заказ не найден."
        message_type = "danger"
    else:
        results = db.query(Result).filter(Result.order_id == order.id).all()
        for result in results:
            db.delete(result)

        db.delete(order)
        db.commit()
        message = "Заказ удалён успешно!"
        message_type = "success"

    orders = db.query(Order).order_by(Order.id.desc()).all()
    return templates.TemplateResponse("manager.html", {
        "request": request,
        "orders": orders,
        "message": message,
        "message_type": message_type,
        "user": current_user,
        "role": current_user.role.value,
    })



@app.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request, current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    check_role_access(current_user, {Role.superuser, Role.admin})
    # Проверяем, есть ли настройки в базе данных
    settings = db.query(Settings).order_by(Settings.id.desc()).all()

    if not settings:
        # Создаем экземпляр настроек с предопределенными значениями
        default_settings = Settings(
            updated_at=date.today(),  # Используем текущую дату
            blueback_price_m2=46.20,
            banner_molded_price_m2=141.63,
            banner_laminated_price_m2=86.91,
            mesh_price_m2=108.91,
            # blueback_price_roll=21900,
            # banner_molded_price_roll=22660,
            # banner_laminated_price_roll=13905,
            # mesh_price_roll=17425,
            eyelet_step=0.28,
            eyelet_price=1.39,
            paint_price_liter=950,
            paint_consumption_m2=0.015,
            print_price_m2=14.25,
            printer_rate_m2=20,
            eyelet_rate=5,
            cutter_rate_m2=2.78,
            payer_rate=50,
        )
        db.add(default_settings)
        db.commit()

    settings = db.query(Settings).order_by(Settings.id.desc()).all()

    # Обновляем список настроек
    actual_settings = settings[0] if settings else None
    # Передаем настройки в шаблон
    return templates.TemplateResponse("settings.html",
                                      {"request": request,
                                       "user": current_user,
                                       "role": current_user.role.value,
                                       "settings": settings,
                                       "actual_settings": actual_settings
                                       })



@app.post('/create_settings')
async def create_settings(request: Request, db: Session = Depends(get_db)):
    # Получаем данные из формы
    form_data = await request.form()  # Используем await для получения данных

    blueback_price_m2 = form_data.get('blueback_price_m2')
    banner_molded_price_m2 = form_data.get('banner_molded_price_m2')
    banner_laminated_price_m2 = form_data.get('banner_laminated_price_m2')
    mesh_price_m2 = form_data.get('mesh_price_m2')
    # blueback_price_roll = form_data.get('blueback_price_roll')
    # banner_molded_price_roll = form_data.get('banner_molded_price_roll')
    # banner_laminated_price_roll = form_data.get('banner_laminated_price_roll')
    # mesh_price_roll = form_data.get('mesh_price_roll')
    eyelet_step = form_data.get('eyelet_step')
    eyelet_price = form_data.get('eyelet_price')
    paint_price_liter = form_data.get('paint_price_liter')
    paint_consumption_m2 = form_data.get('paint_consumption_m2')
    print_price_m2 = form_data.get('print_price_m2')
    printer_rate_m2 = form_data.get('printer_rate_m2')
    eyelet_rate = form_data.get('eyelet_rate')
    cutter_rate_m2 = form_data.get('cutter_rate_m2')
    payer_rate = form_data.get('payer_rate')

    # Создаем новый объект настроек
    new_setting = Settings(
        updated_at=datetime.now(),
        blueback_price_m2=float(blueback_price_m2),
        banner_molded_price_m2=float(banner_molded_price_m2),
        banner_laminated_price_m2=float(banner_laminated_price_m2),
        mesh_price_m2=float(mesh_price_m2),
        # blueback_price_roll=float(blueback_price_roll),
        # banner_molded_price_roll=float(banner_molded_price_roll),
        # banner_laminated_price_roll=float(banner_laminated_price_roll),
        # mesh_price_roll=float(mesh_price_roll),
        eyelet_step=float(eyelet_step),
        eyelet_price=float(eyelet_price),
        paint_price_liter=float(paint_price_liter),
        paint_consumption_m2=float(paint_consumption_m2),
        print_price_m2=float(print_price_m2),
        printer_rate_m2=float(printer_rate_m2),
        eyelet_rate=float(eyelet_rate),
        cutter_rate_m2=float(cutter_rate_m2),
        payer_rate=float(payer_rate)
    )

    # Добавляем новую запись в базу данных
    db.add(new_setting)
    db.commit()

    # Перенаправляем обратно на страницу с настройками
    return RedirectResponse(url='/settings', status_code=303)


app.include_router(admin_router, prefix="/admin", dependencies=[Depends(get_current_user)])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

