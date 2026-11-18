from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Замените строку подключения на вашу PostgreSQL (например: postgresql+psycopg2://user:password@localhost/dbname)
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/vehicle_service_db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()