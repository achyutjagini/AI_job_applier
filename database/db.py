"""Database operations for job postings."""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, inspect, func
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

from database.models import Base, Job, JobSchema
from utils.config import DATABASE_URL, DATABASE_PATH

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize the database and create tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized at {DATABASE_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def job_exists(url: str, db: Optional[Session] = None) -> bool:
    """Check if a job already exists in the database by URL.
    
    Args:
        url: Job URL
        db: Database session (optional)
        
    Returns:
        bool: True if job exists, False otherwise
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        result = db.query(Job).filter(Job.url == url).first()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking if job exists: {e}")
        return False
    finally:
        if close_session:
            db.close()


def insert_job(job_data: JobSchema, db: Optional[Session] = None) -> Optional[Job]:
    """Insert a new job into the database.
    
    Args:
        job_data: JobSchema instance with job data
        db: Database session (optional)
        
    Returns:
        Job: Created Job object or None if failed
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Check if job already exists
        if job_exists(job_data.url, db):
            logger.debug(f"Job already exists: {job_data.url}")
            return None

        # Create and insert job
        db_job = Job(**job_data.dict())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Inserted job: {db_job.title} at {db_job.company}")
        return db_job
    except Exception as e:
        logger.error(f"Error inserting job: {e}")
        db.rollback()
        return None
    finally:
        if close_session:
            db.close()


def get_all_jobs(db: Optional[Session] = None) -> List[Job]:
    """Retrieve all jobs from the database.
    
    Args:
        db: Database session (optional)
        
    Returns:
        List[Job]: List of all jobs
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        jobs = db.query(Job).all()
        return jobs
    except Exception as e:
        logger.error(f"Error retrieving jobs: {e}")
        return []
    finally:
        if close_session:
            db.close()


def get_job_count(db: Optional[Session] = None) -> int:
    """Get total number of jobs in database.
    
    Args:
        db: Database session (optional)
        
    Returns:
        int: Total number of jobs
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        count = db.query(func.count(Job.id)).scalar()
        return count
    except Exception as e:
        logger.error(f"Error getting job count: {e}")
        return 0
    finally:
        if close_session:
            db.close()


def get_job_count(db: Optional[Session] = None) -> int:
    """Get total number of jobs in database.
    
    Args:
        db: Database session (optional)
        
    Returns:
        int: Total number of jobs
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        count = db.query(Job).count()
        return count
    except Exception as e:
        logger.error(f"Error getting job count: {e}")
        return 0
    finally:
        if close_session:
            db.close()


def get_db_stats(db: Optional[Session] = None) -> Dict[str, Any]:
    """Get database statistics.
    
    Args:
        db: Database session (optional)
        
    Returns:
        Dict: Statistics about jobs in database
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        total_jobs = db.query(func.count(Job.id)).scalar()
        
        # Count by source
        source_counts = db.query(Job.source, func.count(Job.id)).group_by(Job.source).all()
        by_source = {source: count for source, count in source_counts}
        
        return {
            "total_jobs": total_jobs,
            "by_source": by_source
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {"total_jobs": 0, "by_source": {}}
    finally:
        if close_session:
            db.close()


def get_jobs_by_source(source: str, db: Optional[Session] = None) -> List[Job]:
    """Retrieve jobs by source.
    
    Args:
        source: Job source name
        db: Database session (optional)
        
    Returns:
        List[Job]: List of jobs from the specified source
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        jobs = db.query(Job).filter(Job.source == source).all()
        return jobs
    except Exception as e:
        logger.error(f"Error retrieving jobs by source: {e}")
        return []
    finally:
        if close_session:
            db.close()
