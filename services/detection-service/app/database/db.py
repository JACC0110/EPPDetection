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

    # Postgres supports ALTER TABLE ... ADD COLUMN IF NOT EXISTS.
    with engine.begin() as conn:
        for column, ddl in [
            ("video_id", "TEXT"),
            ("video_time", "DOUBLE PRECISION"),
            ("person", "BOOLEAN"),
            ("helmet", "BOOLEAN"),
            ("vest", "BOOLEAN"),
            ("gloves", "BOOLEAN"),
            ("goggles", "BOOLEAN"),
            ("mask", "BOOLEAN"),
            ("compliance", "BOOLEAN"),
            ("bbox_x1", "INTEGER"),
            ("bbox_y1", "INTEGER"),
            ("bbox_x2", "INTEGER"),
            ("bbox_y2", "INTEGER"),
            ("image_path", "TEXT"),
            ("required_items", "JSON"),
            ("missing_items", "JSON"),
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