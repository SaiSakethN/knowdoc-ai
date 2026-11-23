"""Initial schema, vector extension and FTS trigger.

Revision ID: 0001
"""
from alembic import op

from knowdoc import models  # noqa: F401
from knowdoc.db import Base

revision = "0001"
down_revision = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(op.get_bind(), tables=[t for t in Base.metadata.sorted_tables if t.name not in {"evaluation_tasks", "source_files"}], checkfirst=False)
    op.execute("""CREATE FUNCTION knowdoc_chunk_fts() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN NEW.search_vector := to_tsvector('english', NEW.text); RETURN NEW; END $$""")
    op.execute("""CREATE TRIGGER chunks_fts BEFORE INSERT OR UPDATE OF text ON chunks
    FOR EACH ROW EXECUTE FUNCTION knowdoc_chunk_fts()""")


def downgrade():
    Base.metadata.drop_all(op.get_bind())
    op.execute("DROP FUNCTION IF EXISTS knowdoc_chunk_fts()")
