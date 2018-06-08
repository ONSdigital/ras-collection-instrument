import logging
import structlog

from flask import current_app
from functools import wraps

from application.exceptions import RasDatabaseError, RasError

log = structlog.wrap_logger(logging.getLogger(__name__))


def with_db_session(f):
    """
    Wraps the supplied function, and introduces a correctly-scoped database session which is passed into the decorated
    function as the named parameter 'session'.

    :param f: The function to be wrapped.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        log.info("Acquiring database session.",
                 pool_size=current_app.db.engine.pool.size(),
                 connections_in_pool=current_app.db.engine.pool.checkedin(),
                 connections_checked_out=current_app.db.engine.pool.checkedout(),
                 current_overflow=current_app.db.engine.pool.overflow()
                 )
        session = current_app.db.session()
        try:
            result = f(*args, **kwargs, session=session)
            log.debug("Committing database session.")
            session.commit()
            return result
        except RasError:
            log.exception("Rolling-back database session.")
            session.rollback()
            raise
        except Exception as e:
            log.exception("Rolling-back database session.")
            session.rollback()
            raise RasDatabaseError("There was an error committing the changes to the database. Details: {}".format(e))
        finally:
            log.debug("Removing database session.")
            current_app.db.session.remove()
    return wrapper
