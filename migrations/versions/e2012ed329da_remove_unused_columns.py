"""remove unused columns from exercise table

Revision ID: e2012ed329da
Revises: d975ea83b712
Create Date: 2021-10-21 10:01:56.565921

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.types import Enum, Integer

# revision identifiers, used by Alembic.
revision = "e2012ed329da"
down_revision = "d975ea83b712"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("exercise", "items", schema="ras_ci")
    op.drop_column("exercise", "status", schema="ras_ci")


def downgrade():
    op.add_column("exercise", sa.Column("items", Integer), schema="ras_ci")
    op.add_column(
        "exercise",
        sa.Column("status", Enum("uploading", "pending", "active", name="status")),
        schema="ras_ci",
    )
