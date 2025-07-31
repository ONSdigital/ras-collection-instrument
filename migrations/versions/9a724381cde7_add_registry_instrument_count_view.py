"""Create view ras_ci.registry_instrument_count

Revision ID: 9a724381cde7
Revises: b730b3a81f72
Create Date: 2025-07-08 13:26:12.483442

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9a724381cde7"
down_revision = "b730b3a81f72"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE VIEW ras_ci.registry_instrument_count as SELECT exercise_id, count(*) as count
        FROM ras_ci.registry_instrument GROUP BY exercise_id; """
    )


def downgrade():
    op.execute("""DROP VIEW registry_instrument_count""")
