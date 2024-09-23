from sqlalchemy import create_engine, Column, Integer, String, Enum, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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
    role = Column(Enum(Role), index=True)     # Роль пользователя

# Описание модели материала
class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)                        # Название
    price_per_sqm = Column(Numeric(10, 2))                  # Цена на кв.м
    width = Column(Numeric(5, 2))                            # Ширина
    length = Column(Integer)                                 # Длина
    roll_cost = Column(Numeric(10, 2))                      # Стоимость рулона
    note = Column(String)                                    # Примечание

# Описание модели комплектующих
class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)                        # Название
    price_per_unit = Column(Numeric(10, 2))                 # Цена за штуку

# Описание модели краски
class Paint(Base):
    __tablename__ = "paints"

    id = Column(Integer, primary_key=True, index=True)
    price_per_liter = Column(Numeric(10, 2))                # Стоимость литра
    consumption_per_sqm = Column(Numeric(10, 3))            # Расход (л)
    price_per_sqm_printing = Column(Numeric(10, 2))         # Цена за кв.м печати

# Описание модели дополнительной опции
class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    option = Column(String, index=True)                      # Опция (да/нет)

# Описание модели шага люверса
class GrommetStep(Base):
    __tablename__ = "grommet_steps"

    id = Column(Integer, primary_key=True, index=True)
    step_size = Column(Numeric(5, 2))                        # Шаг люверса (м)

# Описание модели исполнителя
class Executor(Base):
    __tablename__ = "executors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)                        # Имя исполнителя

# Описание модели ставок
class Rates(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True, index=True)
    print_rate_per_sqm = Column(Numeric(10, 2))            # Ставка печатника за кв.м
    grommet_rate = Column(Numeric(10, 2))                   # Ставка за люверс
    cutter_rate_per_sqm = Column(Numeric(10, 2))            # Ставка резчика за кв.м
    welder_rate = Column(Numeric(10, 2))                    # Ставка пайщика

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

