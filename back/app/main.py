from fastapi import FastAPI

from app.auth.routers import router as auth_router
from app.bookings.routers import router as bookings_router
from app.companies.routers import router as companies_router

app = FastAPI(title="Autobooking API")

app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(bookings_router)


@app.get("/")
async def root():
    return {"status": "Приложение запущено"}
