from contextlib import contextmanager
from ons_ras_common import ons_env
from .exceptions import SessionScopeException


@contextmanager
def session_scope():
    session = ons_env.db.session
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise SessionScopeException('session failed to commit: ' + str(e))
    finally:
        session.close()
