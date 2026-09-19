# Database engine, session factory, and connection helpers.

from sqlalchemy import create_engine, text
import warnings
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# SQLAlchemy engine connects the app to the configured database.
# If the configured DB driver is not installed (e.g. psycopg2 for Postgres),
# fall back to an in-memory SQLite engine so tests and local runs continue.
try:
    engine = create_engine(DATABASE_URL)
except ModuleNotFoundError as exc:
    warnings.warn(
        f"Failed to create engine for DATABASE_URL={DATABASE_URL!r}: {exc}. "
        "Falling back to in-memory SQLite for testing.",
    )
    engine = create_engine("sqlite:///:memory:")

# SessionLocal creates a new database session per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def get_db():
    """
    FastAPI dependency that provides a database session.
    The session is always closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in the models package."""
    # Import models so SQLAlchemy registers them with Base.metadata
    from app.models import (  # noqa: F401
        chat_history,
        document,
        extracted_text,
        generated_content,
        user,
        workspace,
    )

    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Return True if PostgreSQL responds to a simple query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
