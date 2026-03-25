from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:123456789@localhost:5432/ppe_detection"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_schema():
    """Ensure the database schema has the columns introduced by recent changes."""

    with engine.begin() as conn:
        for column, ddl in [
            ("persona", "BOOLEAN"),
            ("casco", "BOOLEAN"),
            ("chaleco", "BOOLEAN"),
            ("guantes", "BOOLEAN"),
            ("gafas", "BOOLEAN"),
            ("mascarilla", "BOOLEAN"),
            ("cumplimiento", "BOOLEAN"),
            ("ruta_imagen", "TEXT"),
            ("requeridos", "JSON"),
            ("faltantes", "JSON"),
            ("video_time", "DOUBLE PRECISION"),
        ]:
            conn.execute(
                text(
                    f"ALTER TABLE IF EXISTS detections ADD COLUMN IF NOT EXISTS {column} {ddl}"
                )
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()