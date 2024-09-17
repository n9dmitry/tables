from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship  # Добавьте sessionmaker здесь
import enum
from sqlalchemy.exc import IntegrityError

DATABASE_URL = "sqlite:///./database.db"
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

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_number = Column(Integer, nullable=True)
    date = Column(String, nullable=True)  # Дата
    subject = Column(String, nullable=True)  # Сюжет
    material = Column(String, nullable=True)  # Материал
    quantity = Column(Integer, nullable=True)  # Кол-во
    performer = Column(String, nullable=True)  # Исполнитель
    print_width = Column(Float, nullable=True)  # Ширина (печати)
    print_height = Column(Float, nullable=True)  # Высота (печати)
    canvas_width = Column(Float, nullable=True)  # Ширина (канвас)
    canvas_length = Column(Float, nullable=True)  # Длина (канвас)
    eyelets = Column(String, nullable=True)  # Люверсы
    spike = Column(String, nullable=True)  # Спайка
    reinforcement = Column(String, nullable=True)  # Усиление
    customer = Column(String, nullable=False)  # Заказчик
    price_per_unit = Column(Float, nullable=False)  # Цена за ед
    total_amount = Column(Float, nullable=False)  # Сумма