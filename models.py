
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship(
        "ResearchReport",
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(500), nullable=False)
    report = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="reports")
