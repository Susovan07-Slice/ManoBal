from db.base import Base
from db.session import engine
import db.models  # Ensures all models are registered with Base.metadata
from core.config import logger
from sqlalchemy import text, inspect

def init_db():
    """Initializes all database tables defined in metadata and ensures columns are synced."""
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    # Safe schema migration: ensure newly added columns exist in welfare_recommendations
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "welfare_recommendations" in inspector.get_table_names():
                columns = [c["name"] for c in inspector.get_columns("welfare_recommendations")]
                column_defs = [
                    ("title", "VARCHAR(128)"),
                    ("description", "TEXT"),
                    ("reason", "TEXT"),
                    ("evidence_json", "TEXT"),
                    ("source_signals_json", "TEXT"),
                    ("recommended_review_window", "VARCHAR(64)"),
                    ("confidence", "VARCHAR(16) DEFAULT 'MEDIUM'"),
                    ("dedup_hash", "VARCHAR(128)"),
                    ("linked_alert_id", "INTEGER"),
                    ("linked_anomaly_id", "INTEGER"),
                    ("linked_intervention_id", "INTEGER"),
                    ("acknowledged_at", "TIMESTAMP"),
                    ("acknowledged_by", "INTEGER"),
                    ("actioned_at", "TIMESTAMP"),
                    ("actioned_by", "INTEGER"),
                    ("action_notes", "TEXT"),
                    ("updated_at", "TIMESTAMP"),
                ]
                for col_name, col_type in column_defs:
                    if col_name not in columns:
                        try:
                            conn.execute(text(f"ALTER TABLE welfare_recommendations ADD COLUMN {col_name} {col_type}"))
                            logger.info(f"Added missing column {col_name} to welfare_recommendations table.")
                        except Exception as e:
                            logger.warning(f"Could not add column {col_name}: {e}")
                conn.commit()
    except Exception as err:
        logger.warning(f"Schema column sync check encountered error: {err}")
        
    logger.info("Database schema initialized successfully.")

if __name__ == "__main__":
    init_db()

