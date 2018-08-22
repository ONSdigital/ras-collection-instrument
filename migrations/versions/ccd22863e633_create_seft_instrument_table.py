"""create seft instrument table

Revision ID: ccd22863e633
Revises: 72912058602c
Create Date: 2018-02-20 13:22:14.773113

"""
import sqlalchemy as sa
from alembic import op

from application.models import GUID

# revision identifiers, used by Alembic.
revision = 'ccd22863e633'
down_revision = '72912058602c'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    sql_query = "ALTER TABLE ras_ci.instrument ADD CONSTRAINT U_instrument_id UNIQUE(instrument_id)"
    conn.execute(sql_query)

    op.create_table(
        'seft_instrument',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('data', sa.LargeBinary),
        sa.Column('len', sa.Integer),
        sa.Column('file_name', sa.String(32)),
        sa.Column('instrument_id', GUID),
        sa.ForeignKeyConstraint(['instrument_id'], ['ras_ci.instrument.instrument_id']),
        schema='ras_ci'
    )

    sql_query = "INSERT INTO ras_ci.seft_instrument (instrument_id, data, file_name, len) " \
                "SELECT instrument_id, data, file_name, len FROM ras_ci.instrument"
    conn.execute(sql_query)

    op.drop_column('instrument', 'file_name', schema='ras_ci')
    op.drop_column('instrument', 'data', schema='ras_ci')
    op.drop_column('instrument', 'len', schema='ras_ci')

    op.add_column('instrument',
                  sa.Column('type', sa.String(8)),
                  schema='ras_ci'
                  )

    sql_query = "UPDATE ras_ci.instrument SET type = 'SEFT'"
    conn.execute(sql_query)


def downgrade():
    pass
