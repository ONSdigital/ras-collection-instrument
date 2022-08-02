"""Remove SEFT data column

Revision ID: 497436b61d0c
Revises: e2012ed329da
Create Date: 2022-08-02 14:34:23.676426

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "497436b61d0c"
down_revision = "e2012ed329da"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("instrument", "data", schema="ras_ci")


def downgrade():
    op.add_column("instrument", sa.Column("data", postgresql.BYTEA(), nullable=True), schema="ras_ci")
