"""Durable private originals and genuine keyword-only indexes without fake vectors."""
from alembic import op
from sqlalchemy import text

from knowdoc.models import SourceFile

revision = "0003"
down_revision = "0002"


def upgrade():
    # Always create in the migration's current schema. A checkfirst search can
    # incorrectly find a public table while migrating an isolated test schema.
    SourceFile.__table__.create(op.get_bind())
    op.alter_column("chunks", "embedding", nullable=True)


def downgrade():
    if op.get_bind().scalar(text("SELECT count(*) FROM chunks WHERE embedding IS NULL")):
        raise RuntimeError("Reindex keyword-only documents before downgrading; source data will not be deleted")
    op.alter_column("chunks", "embedding", nullable=False)
    op.drop_table("source_files")
