from sqlalchemy.orm import Session, joinedload

from .auth import hash_password
from .config import get_settings
from .database import Base, SessionLocal, engine
from .models import NavCategory, NavItem, User


PUBLIC_NAV = [
    {
        "name": "Development",
        "items": [
            {"title": "Vue", "url": "https://vuejs.org/", "description": "Vue 官方文档", "sort_order": 1},
            {"title": "FastAPI", "url": "https://fastapi.tiangolo.com/", "description": "FastAPI 官方文档", "sort_order": 2},
        ],
    },
    {
        "name": "Tools",
        "items": [
            {"title": "GitHub", "url": "https://github.com/", "description": "代码托管平台", "sort_order": 1},
            {"title": "Vite", "url": "https://vite.dev/", "description": "前端构建工具", "sort_order": 2},
        ],
    },
]

PRIVATE_NAV = [
    {
        "name": "Team Resources",
        "items": [
            {"title": "Linear", "url": "https://linear.app/", "description": "任务跟踪", "sort_order": 1},
            {"title": "Notion", "url": "https://www.notion.so/", "description": "内部文档", "sort_order": 2},
        ],
    },
    {
        "name": "Operations",
        "items": [
            {"title": "Cloudflare", "url": "https://dash.cloudflare.com/", "description": "边缘与 DNS", "sort_order": 1},
            {"title": "Sentry", "url": "https://sentry.io/", "description": "错误监控", "sort_order": 2},
        ],
    },
]


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_defaults(db: Session) -> None:
    settings = get_settings()

    admin = db.query(User).filter(User.username == settings.default_admin_username).first()
    if admin is None:
        db.add(
            User(
                username=settings.default_admin_username,
                password_hash=hash_password(settings.default_admin_password),
                is_active=True,
                is_admin=True,
            )
        )
        db.commit()

    has_categories = db.query(NavCategory).first()
    if has_categories:
        return

    for category_data in PUBLIC_NAV:
        category = NavCategory(name=category_data["name"], is_private=False)
        db.add(category)
        db.flush()
        for item in category_data["items"]:
            db.add(NavItem(category_id=category.id, **item))

    for category_data in PRIVATE_NAV:
        category = NavCategory(name=category_data["name"], is_private=True)
        db.add(category)
        db.flush()
        for item in category_data["items"]:
            db.add(NavItem(category_id=category.id, **item))

    db.commit()


def init_database() -> None:
    create_tables()
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()


def fetch_categories(db: Session, is_private: bool) -> list[NavCategory]:
    return (
        db.query(NavCategory)
        .options(joinedload(NavCategory.items))
        .filter(NavCategory.is_private == is_private)
        .order_by(NavCategory.name.asc())
        .all()
    )


if __name__ == "__main__":
    init_database()

