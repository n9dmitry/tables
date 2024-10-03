from typing import List

from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import enum
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped

DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Role(str, enum.Enum):
    superuser = "Суперпользователь"
    admin = "Администратор"
    manager = "Менеджер"
    printer = "Печатник"
    guest = "Гость"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    login = Column(String, unique=True, index=True)
    role = Column(Enum(Role), index=True)

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_number = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    subject = Column(String, nullable=False)
    material = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    performer = Column(String, nullable=False)
    print_width = Column(Numeric(10, 2), nullable=False)
    print_height = Column(Numeric(10, 2), nullable=False)
    canvas_width = Column(Numeric(10, 2), nullable=False)
    canvas_length = Column(Numeric(10, 2), nullable=False)
    eyelets = Column(String, nullable=False)
    spike = Column(String, nullable=False)
    reinforcement = Column(String, nullable=False)
    customer = Column(String, nullable=True)
    price_per_unit = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)

    result: Mapped["Result"] = relationship(back_populates="order")

class Result(Base):
    __tablename__ = 'results'

    order_id = Column(Integer, ForeignKey('orders.id'), primary_key=True)
    total_print_area = Column(Numeric(10, 2), nullable=True)
    total_canvas_area = Column(Numeric(10, 2), nullable=True)
    total_paints = Column(Numeric(10, 2), nullable=True)
    total_eyelets = Column(Integer, nullable=True)
    total_spikes = Column(Integer, nullable=True)
    total_reinforcements = Column(Integer, nullable=True)

    expenses_canvas = Column(Numeric(10, 2), nullable=True)
    expenses_prints = Column(Numeric(10, 2), nullable=True)
    expenses_eyelets = Column(Numeric(10, 2), nullable=True)
    expenses_reinforcements = Column(Numeric(10, 2), nullable=True)
    salary_printer = Column(Numeric(10, 2), nullable=True)
    salary_eyelet_worker = Column(Numeric(10, 2), nullable=True)
    salary_cutter = Column(Numeric(10, 2), nullable=True)
    salary_welder = Column(Numeric(10, 2), nullable=True)
    total_expenses = Column(Numeric(10, 2), nullable=True)
    tax = Column(Numeric(10, 2), nullable=True)
    margin = Column(Numeric(10, 2), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="result")


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    updated_at = Column(Date, nullable=False)

    blueback_price_m2 = Column(Numeric(10, 2))  # Цена м² блюбэка
    banner_molded_price_m2 = Column(Numeric(10, 2))  # Цена м² баннера литого 450г
    banner_laminated_price_m2 = Column(Numeric(10, 2))  # Цена м² баннера ламинат 440г
    mesh_price_m2 = Column(Numeric(10, 2))  # Цена м² сетки

    blueback_price_roll = Column(Numeric(10, 2))  # Стоимость рулона блюбэка
    banner_molded_price_roll = Column(Numeric(10, 2))  # Стоимость рулона баннера литого 450г
    banner_laminated_price_roll = Column(Numeric(10, 2))  # Стоимость рулона баннера ламинат 440г
    mesh_price_roll = Column(Numeric(10, 2))  # Стоимость рулона сетки

    eyelet_step = Column(Numeric(10, 2))  # Шаг люверса (м)
    eyelet_price = Column(Numeric(10, 2))  # Цена люверса

    paint_price_liter = Column(Numeric(10, 2))  # Цена литра краски
    paint_consumption_m2 = Column(Numeric(10, 2))  # Расход краски на м²
    print_price_m2 = Column(Numeric(10, 2))  # Цена печати за м²

    printer_rate_m2 = Column(Numeric(10, 2))  # Ставка печатника за м²
    eyelet_rate = Column(Numeric(10, 2))  # Ставка за люверс
    cutter_rate_m2 = Column(Numeric(10, 2))  # Ставка резчика за м²
    payer_rate = Column(Numeric(10, 2))  # Ставка пайщика

Base.metadata.create_all(bind=engine)

def create_superuser(db: Session):
    superuser = User(
        name="admin",
        surname="adminov",
        email="admin@example.com",
        password="admin",
        login="admin",
        role=Role.superuser
    )
    try:
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
    except IntegrityError:
        db.rollback()

