from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import authenticate_user, create_access_token, get_current_user
from .config import get_settings
from .database import get_db
from .schemas import LoginRequest, NavCategoryResponse, TokenResponse, UserResponse
from .seed import fetch_categories, init_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


settings = get_settings()
app = FastAPI(title="Nav Site API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return TokenResponse(access_token=create_access_token(user.username))


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user


@app.get("/api/nav/public", response_model=list[NavCategoryResponse])
def get_public_navigation(db: Session = Depends(get_db)):
    return fetch_categories(db, is_private=False)


@app.get("/api/nav/private", response_model=list[NavCategoryResponse])
def get_private_navigation(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return fetch_categories(db, is_private=True)

