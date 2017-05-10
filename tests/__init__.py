from sqlalchemy import create_engine
import testing.postgresql
from application import settings
import psycopg2
import os


# Launch new PostgreSQL server
Postgres = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)
postgresql = Postgres()
settings.SQLALCHEMY_DATABASE_URI = postgresql.url()
create_engine(postgresql.url())
conn = psycopg2.connect(**postgresql.dsn())
cursor = conn.cursor()
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sql_build = open(os.path.join(ROOT_DIR, 'ras_collection_instrument_D0001_initial_build.sql')).read()
cursor.execute(sql_build)

conn.commit()
conn.close()
