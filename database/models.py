"""Database models for job postings."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()


class Job(Base):
    """SQLAlchemy model for job postings."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), index=True, nullable=False)
    company = Column(String(256), index=True, nullable=False)
    location = Column(String(256), nullable=True)
    url = Column(String(512), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    date_posted = Column(DateTime, nullable=True)
    source = Column(String(50), index=True, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, company={self.company}, source={self.source})>"


class JobSchema(BaseModel):
    """Pydantic schema for job validation."""

    title: str
    company: str
    location: Optional[str] = None
    url: str
    description: Optional[str] = None
    date_posted: Optional[datetime] = None
    source: str
    scraped_at: datetime
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        from_attributes = True

    def __repr__(self) -> str:
        return f"<JobSchema(title={self.title}, company={self.company}, source={self.source})>"
