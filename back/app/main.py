from fastapi import FastAPI

from app.auth.routers import router as auth_router

app = FastAPI(title="Autobooking API")

app.include_router(auth_router)


@app.get("/")
async def root():
    return {"status": "Приложение запущено"}
