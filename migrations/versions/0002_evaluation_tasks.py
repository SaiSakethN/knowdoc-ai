"""Durable evaluation queue.

Revision ID: 0002
"""
from alembic import op
from sqlalchemy import text

from knowdoc.models import EvaluationTask

revision = "0002"
down_revision = "0001"


def upgrade():
    EvaluationTask.__table__.create(op.get_bind())
    # Runtime role may not exist on CI/fresh schemas. Restrict grants to public application schema.
    connection = op.get_bind()
    if connection.scalar(text("SELECT current_schema()")) == "public" and connection.scalar(text("SELECT 1 FROM pg_roles WHERE rolname='knowdoc_app'")):
        op.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON evaluation_tasks TO knowdoc_app")


def downgrade():
    EvaluationTask.__table__.drop(op.get_bind())
