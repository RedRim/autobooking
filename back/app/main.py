from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.bookings.routers import router as bookings_router
from app.companies.routers import router as companies_router

app = FastAPI(title="Autobooking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
