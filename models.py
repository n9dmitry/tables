from typing import List

from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Date
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
    print_width = Column(Float, nullable=False)
    print_height = Column(Float, nullable=False)
    canvas_width = Column(Float, nullable=False)
    canvas_length = Column(Float, nullable=False)
    eyelets = Column(String, nullable=False)
    spike = Column(String, nullable=False)
    reinforcement = Column(String, nullable=False)
    customer = Column(String, nullable=True)
    price_per_unit = Column(Integer, nullable=True)
    total_amount = Column(Integer, nullable=True)

    result: Mapped["Result"] = relationship(back_populates="order")

class Result(Base):
    __tablename__ = 'results'

    order_id = Column(Integer, ForeignKey('orders.id'), primary_key=True)
    total_print_area = Column(Float, nullable=True)
    total_canvas_area = Column(Float, nullable=True)
    total_paints = Column(String, nullable=True)
    total_eyelets = Column(Integer, nullable=True)
    total_spikes = Column(Integer, nullable=True)
    total_reinforcements = Column(Integer, nullable=True)

    expenses_canvas = Column(Float, nullable=True)
    expenses_prints = Column(Float, nullable=True)
    expenses_eyelets = Column(Float, nullable=True)
    expenses_reinforcements = Column(Float, nullable=True)
    salary_printer = Column(Float, nullable=True)
    salary_eyelet_worker = Column(Float, nullable=True)
    salary_cutter = Column(Float, nullable=True)
    salary_welder = Column(Float, nullable=True)
    total_expenses = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="result")



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

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
