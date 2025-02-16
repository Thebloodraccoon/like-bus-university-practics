from fastapi import FastAPI  # type: ignore

from app.auth.endpoints import router as auth_router
from app.conf import lifespan
from app.polonus.endpoints import polonus
from app.users.endpoints import router as users_router

app = FastAPI(
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/user", tags=["User"])

app.mount("/polonus", app=polonus)
