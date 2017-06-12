from uuid import uuid4
from structlog import get_logger

logger = get_logger()


def ensure_log_on_error(code, msg):
    if code != 200:
        logger.info("Bad request", error_data=msg)


def bind_request_detail_to_log(request):
    logger.bind(
        tx_id=str(uuid4()),
        method=request.method,
        path=request.full_path
    )
    logger.info("Start request")
