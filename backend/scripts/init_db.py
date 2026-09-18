# backend/scripts/init_db.py
"""Initialize the production database schema.

Creates every table (base + new models) via Base.metadata, enables the
pgvector extension if the host provides it, and stamps Alembic at head so
future `alembic upgrade head` runs are consistent.

Run from the backend/ directory:
    python scripts/init_db.py

DATABASE_URL is read from the environment (or settings' .env in local dev).
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
import app.models  # noqa: F401,E402  (imports every model into Base.metadata)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chuoai-init")


def main() -> None:
    # 1. Enable pgvector (best-effort; not all PostgreSQL hosts have it).
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        logger.info("pgvector extension ensured")
    except Exception as e:
        logger.warning(f"Could not enable pgvector (optional): {e}")

    # 2. Create all tables (create_all uses checkfirst=True by default).
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema created")

    # 3. Stamp Alembic at head so future migrations start from a known point.
    try:
        from alembic.config import Config
        from alembic import command
        cfg = Config(os.path.join(ROOT_DIR, "alembic.ini"))
        cfg.set_main_option("script_location", os.path.join(ROOT_DIR, "backend", "alembic"))
        command.stamp(cfg, "head")
        logger.info("Alembic stamped at head")
    except Exception as e:
        logger.warning(f"Could not stamp alembic (optional, non-fatal): {e}")


if __name__ == "__main__":
    main()