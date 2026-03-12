from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


class NavCategory(Base):
    __tablename__ = "nav_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_private = Column(Boolean, default=False, nullable=False)

    items = relationship("NavItem", back_populates="category", cascade="all, delete-orphan")


class NavItem(Base):
    __tablename__ = "nav_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    category_id = Column(Integer, ForeignKey("nav_categories.id"), nullable=False)

    category = relationship("NavCategory", back_populates="items")

