from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship  # Добавьте sessionmaker здесь
import enum
from sqlalchemy.exc import IntegrityError

# Создаем базу данных
DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Определяем базу данных
Base = declarative_base()

# Перечисление ролей пользователя
class Role(str, enum.Enum):
    superuser = "Суперпользователь"
    admin = "Администратор"
    manager = "Менеджер"
    printer = "Печатник"
    guest = "Гость"

# Описание модели пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)          # Имя
    surname = Column(String, index=True)       # Фамилия
    email = Column(String, unique=True, index=True)  # Email
    password = Column(String)                  # Пароль (обычный текст)
    login = Column(String, unique=True, index=True)  # Логин
    role = Column(Enum(Role), index=True)      # Роль пользователя

# Описание модели заказа
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    task_number = Column(String, index=True)
    date = Column(String)
    plot = Column(String)
    material = Column(String)
    width = Column(Float)
    height = Column(Float)
    eyelets = Column(String)
    spike = Column(String)
    reinforcement = Column(String)
    quantity = Column(Integer)
    customer = Column(String)
    price_per_unit = Column(Float)
    total_amount = Column(Float)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Функция для создания суперпользователя
def create_superuser(db: Session):
    superuser = User(
        name="admin",
        surname="adminov",
        email="admin@example.com",
        password="admin",
        login="admin",
        role=Role.superuser  # Задаем роль суперпользователя
    )
    try:
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
    except IntegrityError:
        db.rollback()  # В случае ошибки, откатим изменения