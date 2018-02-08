import functools
import logging
import structlog

from flask import current_app
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit import ExchangePublisher, QueuePublisher

from application.controllers.json_encrypter import Encrypter


log = structlog.wrap_logger(logging.getLogger(__name__))


def encrypt_message(message_json):
    """
    Encrypts a JSON message
    :param message_json: The file in JSON format
    :return: jwe as String
    """
    log.info('Encrypting JSON message')
    json_secret_keys = current_app.config['JSON_SECRET_KEYS']
    encrypter = Encrypter(json_secret_keys)
    return encrypter.encrypt(message_json)


def send_message_to_rabbitmq(message, tx_id, queue_name, encrypt=True, use_exchange=False):
    """
    Get details from environment credentials and send message to rabbitmq
    :param message: The message to send to the queue in JSON format
    :param tx_id: The transaction ID for the message
    :param queue_name: The rabbit queue to publish to
    :param encrypt: Flag whether message should be encrypted before publication
    :return: boolean
    """
    rabbitmq_amqp = current_app.config['RABBITMQ_AMQP']
    log.debug('Connecting to rabbitmq', url=rabbitmq_amqp)
    publisher_type = ExchangePublisher if use_exchange else QueuePublisher
    publisher = publisher_type([rabbitmq_amqp], queue_name)
    message = encrypt_message(message) if encrypt else message
    try:
        result = publisher.publish_message(message, headers={"tx_id": tx_id}, immediate=False, mandatory=True)
        log.info('Message successfully sent to rabbitmq', tx_id=tx_id, queue=queue_name)
        return result
    except PublishMessageError:
        log.exception('Message failed to send to rabbitmq', tx_id=tx_id)
        return False


send_message_to_rabbitmq_queue = functools.partial(send_message_to_rabbitmq, use_exchange=False)
send_message_to_rabbitmq_exchange = functools.partial(send_message_to_rabbitmq, use_exchange=True)
