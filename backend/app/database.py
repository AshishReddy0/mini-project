# Database engine, session factory, and connection helpers.

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# SQLAlchemy engine connects the app to PostgreSQL
engine = create_engine(DATABASE_URL)

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

    # Safely alter content_type_enum in PostgreSQL to support 'logic_flow' if it exists and needs it
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS ( "
                "  SELECT 1 FROM pg_type t "
                "  JOIN pg_enum e ON t.oid = e.enumtypid "
                "  WHERE t.typname = 'content_type_enum' AND e.enumlabel = 'logic_flow' "
                ")"
            ))
            exists = result.scalar()
            if not exists:
                conn.execute(text("COMMIT"))  # close active transaction
                conn.execute(text("ALTER TYPE content_type_enum ADD VALUE 'logic_flow'"))
    except Exception:
        # Silently fail if not running on Postgres, or schema does not have the type yet, or type already altered
        pass

    # Safely add new columns to concept_nodes if they don't exist yet
    _safe_add_column(engine, "concept_nodes", "sub_points", "jsonb")
    _safe_add_column(engine, "concept_nodes", "answer_cache", "text")


def _safe_add_column(engine, table: str, column: str, col_type: str):
    """Add a column to a table only if it doesn't already exist. Safe for production restarts."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.columns "
                f"  WHERE table_name='{table}' AND column_name='{column}'"
                ")"
            ))
            exists = result.scalar()
            if not exists:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
    except Exception:
        pass


def check_db_connection() -> bool:
    """Return True if PostgreSQL responds to a simple query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
