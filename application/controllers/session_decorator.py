from functools import wraps

from flask import current_app
from ras_common_utils.ras_error.ras_error import RasDatabaseError, RasError
from structlog import get_logger

log = get_logger()


def with_db_session(f):
    """
    Wraps the supplied function, and introduces a correctly-scoped database session which is passed into the decorated
    function as the named parameter 'session'.

    :param f: The function to be wrapped.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        log.info("Acquiring database session.")
        session = current_app.db.session()
        try:
            result = f(*args, **kwargs, session=session)
            log.info("Committing database session.")
            session.commit()
            return result
        except RasError:
            log.info("Rolling-back database session.")
            session.rollback()
            raise
        except Exception as e:
            log.info("Rolling-back database session.")
            session.rollback()
            raise RasDatabaseError("There was an error committing the changes to the database. Details: {}".format(e))
        finally:
            log.info("Removing database session.")
            current_app.db.session.remove()
    return wrapper
