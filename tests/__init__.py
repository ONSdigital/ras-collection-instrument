from application import settings
from sqlalchemy import create_engine

import os
import psycopg2
import testing.postgresql

Postgres = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)
postgresql = Postgres()

settings.SQLALCHEMY_DATABASE_URI = postgresql.url()
create_engine(postgresql.url())

conn = psycopg2.connect(**postgresql.dsn())
cursor = conn.cursor()

sql_build = open(os.path.join(settings.ROOT_DIR, settings.SQL_INITIAL_BUILD)).read()
cursor.execute(sql_build)
conn.commit()
conn.close()
