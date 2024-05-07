"""add seft ci file location column

Revision ID: d975ea83b712
Revises: ccd22863e633
Create Date: 2021-09-06 10:40:27.089307

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.types import Boolean

# revision identifiers, used by Alembic.
revision = "d975ea83b712"
down_revision = "ccd22863e633"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("seft_instrument", sa.Column("gcs", Boolean), schema="ras_ci")


def downgrade():
    op.drop_column("seft_instrument", "gcs")
