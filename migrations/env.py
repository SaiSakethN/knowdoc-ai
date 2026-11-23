from alembic import context
from sqlalchemy import create_engine, text

from knowdoc import models  # noqa: F401
from knowdoc.config import settings
from knowdoc.db import Base

with create_engine(settings().migration_database_url or settings().database_url).connect() as connection:
    schema = connection.scalar(text("SELECT current_schema()"))
    connection.commit()
    context.configure(connection=connection, target_metadata=Base.metadata, version_table_schema=schema)
    with context.begin_transaction():
        context.run_migrations()
