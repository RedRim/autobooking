from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.bookings.routers import router as bookings_router
from app.companies.routers import router as companies_router
from app.config import get_config

app = FastAPI(title="Autobooking API")

_cors_origins = [
    o.strip()
    for o in get_config().settings.cors_origins.split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(bookings_router)


@app.get("/")
async def root():
    return {"status": "Приложение запущено"}
