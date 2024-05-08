"""Remove SEFT data column

Revision ID: f55291dd84c0
Revises: 497436b61d0c
Create Date: 2022-08-10 15:02:35.189420

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f55291dd84c0"
down_revision = "497436b61d0c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("seft_instrument", "gcs", schema="ras_ci")


def downgrade():
    op.add_column("seft_instrument", sa.Column("gcs", postgresql.BOOLEAN(), nullable=True), schema="ras_ci")
