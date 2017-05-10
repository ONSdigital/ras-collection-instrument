from application import settings
from sqlalchemy import create_engine

import os
import psycopg2
import testing.postgresql

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_SCRIPTS = 'sql_scripts'
COLLECTION_INSTRUMENT_BUILD = 'ras_collection_instrument_D0001_initial_build.sql'

Postgres = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)
postgresql = Postgres()

settings.SQLALCHEMY_DATABASE_URI = postgresql.url()

create_engine(postgresql.url())
conn = psycopg2.connect(**postgresql.dsn())
cursor = conn.cursor()

sql_build = open(os.path.join(TEST_DIR, SQL_SCRIPTS + '/' + COLLECTION_INSTRUMENT_BUILD)).read()
cursor.execute(sql_build)
conn.commit()
conn.close()
