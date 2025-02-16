from contextlib import asynccontextmanager

from fastapi import FastAPI  # type: ignore
from fastapi.security import HTTPBearer  # type: ignore
from fastapi_mail import ConnectionConfig  # type: ignore

from app.db import Base, engine
from app.utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Application is shutting down.")


http_bearer = HTTPBearer()
