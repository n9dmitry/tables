from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import enum
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect

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
    date = Column(Date, nullable=False)  # Изменено на Date
    subject = Column(String, nullable=False)  # Сюжет
    material = Column(String, nullable=False)  # Материал
    quantity = Column(Integer, nullable=False)  # Кол-во
    performer = Column(String, nullable=False)  # Исполнитель
    print_width = Column(Float, nullable=False)  # Ширина (печати)
    print_height = Column(Float, nullable=False)  # Высота (печати)
    canvas_width = Column(Float, nullable=False)  # Ширина (канвас)
    canvas_length = Column(Float, nullable=False)  # Длина (канвас)
    eyelets = Column(String, nullable=False)  # Люверсы
    spike = Column(String, nullable=False)  # Спайка
    reinforcement = Column(String, nullable=False)  # Усиление
    customer = Column(String, nullable=True)  # Заказчик
    price_per_unit = Column(Float, nullable=True)  # Цена за ед
    total_amount = Column(Float, nullable=True)  # Сумма

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
