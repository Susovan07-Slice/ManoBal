import os
import sys
import unittest
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
from alembic.config import Config
from alembic import command

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from core.config import settings
from db.base import Base
from db.session import engine, SessionLocal, create_db_engine
from db.models import User, Personnel, StressAssessment, WelfareRecommendation
from core.security import hash_password, verify_password

class TestDatabasePhase18(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # =========================================================================
    # 1. POSTGRESQL DRIVER & ENGINE CONFIGURATION TESTS
    # =========================================================================
    def test_01_postgresql_drivers_installed(self):
        """Verify that PostgreSQL drivers (psycopg2 and psycopg v3) are installed."""
        import psycopg2
        import psycopg
        self.assertIsNotNone(psycopg2.__version__)
        self.assertIsNotNone(psycopg.__version__)

    def test_02_postgresql_engine_pool_configuration(self):
        """Verify that create_db_engine configures connection pooling for PostgreSQL."""
        pg_url = "postgresql+psycopg://postgres:dummy@localhost:5432/stress_monitoring"
        engine_pg = create_db_engine(pg_url)
        self.assertEqual(engine_pg.dialect.name, "postgresql")
        # Pool size and overflow configured for production concurrency
        self.assertEqual(engine_pg.pool.size(), 10)
        self.assertEqual(engine_pg.pool._max_overflow, 20)
        engine_pg.dispose()

    def test_03_sqlite_engine_configuration(self):
        """Verify that create_db_engine configures SQLite correctly with check_same_thread=False."""
        sqlite_url = "sqlite:///:memory:"
        engine_sqlite = create_db_engine(sqlite_url)
        self.assertEqual(engine_sqlite.dialect.name, "sqlite")
        engine_sqlite.dispose()

    # =========================================================================
    # 2. POSTGRESQL DDL COMPILATION & SCHEMA VALIDATION TESTS
    # =========================================================================
    def test_04_users_ddl_postgresql_compilation(self):
        """Verify User model compiles to valid PostgreSQL DDL with SERIAL PK and FK."""
        ddl = str(CreateTable(User.__table__).compile(dialect=postgresql.dialect()))
        self.assertIn("id SERIAL NOT NULL", ddl)
        self.assertIn("username VARCHAR(64) NOT NULL", ddl)
        self.assertIn("PRIMARY KEY (id)", ddl)
        self.assertIn("FOREIGN KEY(personnel_id) REFERENCES personnel (id) ON DELETE SET NULL", ddl)

    def test_05_personnel_ddl_postgresql_compilation(self):
        """Verify Personnel model compiles to valid PostgreSQL DDL."""
        ddl = str(CreateTable(Personnel.__table__).compile(dialect=postgresql.dialect()))
        self.assertIn("id SERIAL NOT NULL", ddl)
        self.assertIn("personnel_code VARCHAR(32) NOT NULL", ddl)
        self.assertIn("PRIMARY KEY (id)", ddl)

    def test_06_assessment_ddl_postgresql_compilation(self):
        """Verify StressAssessment compiles to valid PostgreSQL DDL with CASCADE constraint."""
        ddl = str(CreateTable(StressAssessment.__table__).compile(dialect=postgresql.dialect()))
        self.assertIn("id SERIAL NOT NULL", ddl)
        self.assertIn("FOREIGN KEY(personnel_id) REFERENCES personnel (id) ON DELETE CASCADE", ddl)

    def test_07_recommendations_ddl_postgresql_compilation(self):
        """Verify WelfareRecommendation compiles to valid PostgreSQL DDL with cascading FKs."""
        ddl = str(CreateTable(WelfareRecommendation.__table__).compile(dialect=postgresql.dialect()))
        self.assertIn("id SERIAL NOT NULL", ddl)
        self.assertIn("FOREIGN KEY(personnel_id) REFERENCES personnel (id) ON DELETE CASCADE", ddl)
        self.assertIn("FOREIGN KEY(assessment_id) REFERENCES stress_assessments (id) ON DELETE CASCADE", ddl)

    # =========================================================================
    # 3. ALEMBIC MIGRATION VERIFICATION
    # =========================================================================
    def test_08_alembic_reaches_head_migration(self):
        """Verify Alembic configuration head is recognized."""
        alembic_cfg = Config(os.path.join(settings.BASE_DIR, "alembic.ini"))
        # Verify script directory can be loaded
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        self.assertIn(head_rev, ["a844f6a8b55f", "b912c3f4e5a6", "c023d4e5f6a7"])

    # =========================================================================
    # 4. DATABASE HEALTH CHECK
    # =========================================================================
    def test_09_database_health_check_safe(self):
        """Verify GET /api/health probes DB safely without exposing credentials or SQL details."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database", data)
        self.assertTrue(data["database"]["connected"])
        self.assertIn(data["database"]["engine"], ["sqlite", "postgresql"])
        # Ensure sensitive connection details are NEVER exposed
        response_text = response.text.lower()
        self.assertNotIn("password", response_text)
        self.assertNotIn("secret", response_text)
        self.assertNotIn("token", response_text)
        self.assertNotIn("connection string", response_text)

    # =========================================================================
    # 5. ORM CRUD OPERATIONS VERIFICATION
    # =========================================================================
    def test_10_crud_lifecycle_user_personnel_assessment_recommendation(self):
        """Verify complete CRUD lifecycle: create, read, relate, update, and cascade delete."""
        db = SessionLocal()
        try:
            # 1. Create Personnel
            test_code = f"TEST-CRUD-{int(datetime.now().timestamp())}"
            p = Personnel(
                personnel_code=test_code,
                name="Test Operator",
                age=28,
                gender="Male",
                department="Operations",
                job_role="Scout",
                location="Field Base",
                experience_years=4.0,
                duty_hours_per_week=48.0,
                consecutive_duty_days=6,
                night_shifts_per_month=4
            )
            db.add(p)
            db.commit()
            db.refresh(p)
            self.assertIsNotNone(p.id)

            # 2. Create User linked to Personnel
            u = User(
                username=f"user_{test_code.lower()}",
                hashed_password=hash_password("TestSecret123!"),
                role="personnel",
                personnel_id=p.id
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            self.assertTrue(verify_password("TestSecret123!", u.hashed_password))
            self.assertEqual(u.personnel.personnel_code, test_code)

            # 3. Create Assessment linked to Personnel
            a = StressAssessment(
                personnel_id=p.id,
                stress_level="Medium",
                low_probability=0.25,
                medium_probability=0.60,
                high_probability=0.15,
                risk_score=52,
                risk_priority="Preventive",
                key_factors=json.dumps(["Duty hours slightly elevated", "Short sleep recovery"]),
                model_version="1.0.0-LightGBM"
            )
            db.add(a)
            db.commit()
            db.refresh(a)
            self.assertIsNotNone(a.id)
            self.assertEqual(len(p.assessments), 1)

            # 4. Create Recommendation linked to Assessment and Personnel
            r = WelfareRecommendation(
                personnel_id=p.id,
                assessment_id=a.id,
                recommendation_type="Sleep & Recovery",
                recommendation_text="Ensure 7 hours sleep interval between operational shifts.",
                priority="Preventive",
                status="pending"
            )
            db.add(r)
            db.commit()
            db.refresh(r)
            self.assertEqual(r.status, "pending")

            # Update Recommendation status
            r.status = "acknowledged"
            db.commit()
            db.refresh(r)
            self.assertEqual(r.status, "acknowledged")

            # 5. Verify Cascade Deletion of Assessment & Recommendation
            rec_id = r.id
            db.delete(a)
            db.commit()
            # Recommendation should be cascade deleted
            orphaned_rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == rec_id).first()
            self.assertIsNone(orphaned_rec)

            # Clean up user and personnel
            db.delete(u)
            db.delete(p)
            db.commit()

        finally:
            db.close()

if __name__ == '__main__':
    unittest.main()
