import functools
import logging
import structlog

from flask import current_app
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit import DurableExchangePublisher, QueuePublisher

from application.controllers.json_encrypter import Encrypter


log = structlog.wrap_logger(logging.getLogger(__name__))


def _encrypt_message(message_json):
    """
    Encrypts a JSON message
    :param message_json: The file in JSON format
    :return: jwe as String
    """
    log.info('Encrypting JSON message')
    json_secret_keys = current_app.config['JSON_SECRET_KEYS']
    encrypter = Encrypter(json_secret_keys)
    return encrypter.encrypt(message_json)


def _initialise_rabbitmq(queue_name, publisher_type, rabbitmq_amqp):
    """
    Initialise a rabbit queue or exchange is created ahead of use
    :param queue_name: The rabbit queue or exchange to initialise
    :param publisher_type: Publisher class from sdc-rabbit to use
    :param rabbitmq_amqp: connection string for rabbitmq
    :return: boolean
    """
    log.debug('Connecting to rabbitmq', url=rabbitmq_amqp)
    publisher = publisher_type([rabbitmq_amqp], queue_name)
    # NB: _connect declares a queue or exchange
    publisher._connect()
    log.info('Successfully initialised rabbitmq', queue=queue_name)


def _send_message_to_rabbitmq(message, tx_id, queue_name, publisher_type, rabbitmq_amqp, encrypt=True):
    """
    Send message to rabbitmq
    :param message: The message to send to the queue in JSON format
    :param tx_id: The transaction ID for the message
    :param queue_name: The rabbit queue or exchange to publish to
    :param encrypt: Flag whether message should be encrypted before publication
    :param publisher_type: Publisher class from sdc-rabbit to use
    :param rabbitmq_amqp: connection string for rabbitmq
    :return: boolean
    """
    log.debug('Connecting to rabbitmq', url=rabbitmq_amqp)
    publisher = publisher_type([rabbitmq_amqp], queue_name)
    message = _encrypt_message(message) if encrypt else message
    try:
        result = publisher.publish_message(message, headers={"tx_id": tx_id}, immediate=False, mandatory=True)
        log.info('Message successfully sent to rabbitmq', tx_id=tx_id, queue=queue_name)
        return result
    except PublishMessageError:
        log.exception('Message failed to send to rabbitmq', tx_id=tx_id)
        return False


initialise_rabbitmq_queue = functools.partial(_initialise_rabbitmq, publisher_type=QueuePublisher, rabbitmq_amqp = current_app.config['RABBITMQ_AMQP_SURVEY_RESPONSE'])
initialise_rabbitmq_exchange = functools.partial(_initialise_rabbitmq, publisher_type=DurableExchangePublisher, rabbitmq_amqp = current_app.config['RABBITMQ_AMQP_COLLECTION_INSTRUMENT'])
send_message_to_rabbitmq_queue = functools.partial(_send_message_to_rabbitmq, publisher_type=QueuePublisher, rabbitmq_amqp = current_app.config['RABBITMQ_AMQP_SURVEY_RESPONSE'])
send_message_to_rabbitmq_exchange = functools.partial(_send_message_to_rabbitmq, publisher_type=DurableExchangePublisher, rabbitmq_amqp = current_app.config['RABBITMQ_AMQP_COLLECTION_INSTRUMENT']) # NOQA
