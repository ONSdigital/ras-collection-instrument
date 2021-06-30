"""remove classification table and add file_name and classifiers into instrument

Revision ID: 72912058602c
Create Date: 2018-01-11 15:23:03.943466

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.types import String

# revision identifiers, used by Alembic.
revision = '72912058602c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('instrument',
                  sa.Column('file_name', String(32)),
                  schema='ras_ci'
                  )
    op.add_column('instrument',
                  sa.Column('classifiers', JSONB()),
                  schema='ras_ci'
                  )
    op.drop_table('classification',
                  schema='ras_ci')


def downgrade():
    pass
