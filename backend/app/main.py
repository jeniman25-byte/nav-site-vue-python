from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import authenticate_user, create_access_token, get_admin_user, get_current_user
from .config import get_settings
from .database import get_db
from .models import NavCategory, NavItem
from .schemas import (
    AdminCategoryCreateRequest,
    AdminNavItemCreateRequest,
    LoginRequest,
    NavCategoryResponse,
    TokenResponse,
    UserResponse,
)
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


@app.get("/api/admin/categories", response_model=list[NavCategoryResponse])
def list_admin_categories(db: Session = Depends(get_db), current_user=Depends(get_admin_user)):
    del current_user
    categories = db.query(NavCategory).order_by(NavCategory.is_private.asc(), NavCategory.name.asc()).all()
    for category in categories:
        category.items.sort(key=lambda item: (item.sort_order, item.id))
    return categories


@app.post("/api/admin/categories", response_model=NavCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_admin_category(
    payload: AdminCategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    del current_user
    exists = db.query(NavCategory).filter(NavCategory.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")

    category = NavCategory(name=payload.name, is_private=payload.is_private)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@app.post("/api/admin/nav-items", response_model=NavCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_admin_nav_item(
    payload: AdminNavItemCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    del current_user
    category = db.query(NavCategory).filter(NavCategory.id == payload.category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    item = NavItem(
        title=payload.title,
        url=payload.url,
        description=payload.description,
        sort_order=payload.sort_order,
        category_id=payload.category_id,
    )
    db.add(item)
    db.commit()
    db.refresh(category)
    category.items.sort(key=lambda nav_item: (nav_item.sort_order, nav_item.id))
    return category
