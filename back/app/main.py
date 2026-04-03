from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.bookings.routers import router as bookings_router
from app.companies.routers import router as companies_router
from app.config import get_config

app = FastAPI(title="Autobooking API")

# Локальная разработка (vite / docker-фронт). В проде добавьте домены в CORS_ORIGINS в .env
_DEFAULT_CORS_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:80",
    "http://127.0.0.1:80",
]


def _build_cors_origins() -> list[str]:
    extra = [
        o.strip().rstrip("/")
        for o in get_config().settings.cors_origins.split(",")
        if o.strip()
    ]
    merged = _DEFAULT_CORS_ORIGINS + extra
    return list(dict.fromkeys(merged))


_cfg = get_config()
_cors_regex = (_cfg.settings.cors_origin_regex or "").strip() or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_origin_regex=_cors_regex,
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
