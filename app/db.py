from redis import Redis  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker

from app.constants import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

redis_client = Redis(
    host=settings.HOST_REDIS,
    port=settings.PORT_REDIS,
    db=settings.DB_REDIS,
    decode_responses=True,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    return redis_client
