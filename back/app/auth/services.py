from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zxcvbn import zxcvbn

from app.auth.models import User
from app.auth.schemas import RegisterSchema
from app.config import get_config
from app.database import get_session
from app.auth.models import UserRole

bearer_scheme = HTTPBearer()

_PASSWORD_EXCEPTION = "admin"
_MIN_PASSWORD_LENGTH = 8
_MIN_PASSWORD_SCORE = 3


def _clean_optional_name(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, email: str, role: str) -> str:
    cfg = get_config().jwt
    expire = datetime.now(timezone.utc) + timedelta(minutes=cfg.jwt_expire_minutes)
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def validate_password(password: str, email: str) -> None:
    if password == _PASSWORD_EXCEPTION:
        return

    analysis = zxcvbn(password, user_inputs=[email])
    if analysis.get("score", 0) < _MIN_PASSWORD_SCORE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Пароль слишком простой или часто используемый",
        )

    if len(password) < _MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Пароль должен быть не короче {_MIN_PASSWORD_LENGTH} символов",
        )




async def register_user(data: RegisterSchema, session: AsyncSession, role: UserRole) -> User:
    validate_password(data.password, data.email)

    existing = await session.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже занят")

    user = User(
        email=data.email,
        first_name=_clean_optional_name(data.first_name),
        last_name=_clean_optional_name(data.last_name),
        hashed_password=hash_password(data.password),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    cfg = get_config().jwt
    try:
        payload = jwt.decode(credentials.credentials, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise ValueError
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await session.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user
