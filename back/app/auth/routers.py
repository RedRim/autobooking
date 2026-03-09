from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import LoginSchema, RegisterSchema, TokenResponse, UserResponse
from app.auth.services import authenticate_user, create_access_token, get_current_user, register_user
from app.database import get_session

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterSchema,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await register_user(data, session)
    token = create_access_token(user.id, user.email, user.role.value)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginSchema,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await authenticate_user(data.email, data.password, session)
    token = create_access_token(user.id, user.email, user.role.value)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
