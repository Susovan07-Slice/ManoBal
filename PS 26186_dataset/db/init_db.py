from db.base import Base
from db.session import engine
from db.models import User, Personnel, StressAssessment, WelfareRecommendation
from core.config import logger

def init_db():
    """Initializes all database tables defined in metadata."""
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

if __name__ == "__main__":
    init_db()
