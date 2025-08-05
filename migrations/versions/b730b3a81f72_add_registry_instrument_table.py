"""Add registry_instrument table

Revision ID: b730b3a81f72
Revises: f55291dd84c0
Create Date: 2022-08-10 15:02:35.189420

"""

import sqlalchemy as sqlalchemy
from alembic import op

# revision identifiers, used by Alembic.
revision = "b730b3a81f72"
down_revision = "f55291dd84c0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "registry_instrument",
        sqlalchemy.Column("survey_id", sqlalchemy.UUID, nullable=False),
        sqlalchemy.Column("exercise_id", sqlalchemy.UUID, primary_key=True),
        sqlalchemy.Column("instrument_id", sqlalchemy.UUID, nullable=False),
        sqlalchemy.Column("classifier_type", sqlalchemy.String, primary_key=True),
        sqlalchemy.Column("classifier_value", sqlalchemy.String, primary_key=True),
        sqlalchemy.Column("ci_version", sqlalchemy.Integer, nullable=False),
        sqlalchemy.Column("guid", sqlalchemy.UUID, nullable=False),
        sqlalchemy.Column("published_at", sqlalchemy.TIMESTAMP, nullable=False),
        sqlalchemy.ForeignKeyConstraint(["instrument_id"], ["ras_ci.instrument.instrument_id"]),
        schema="ras_ci",
    )


def downgrade():
    op.drop_table("registry_instrument", schema="ras_ci")
