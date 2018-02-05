import logging
import os
import structlog

from flask import current_app
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit.publisher import QueuePublisher

from application.controllers.json_encrypter import Encrypter


log = structlog.wrap_logger(logging.getLogger(__name__))


def encrypt_message(message_json):
    """
    Encrypts a JSON message
    :param message_json: The file in JSON format
    :return: jwe as String
    """
    log.info('Encrypting JSON message')
    json_secret_keys = os.getenv('JSON_SECRET_KEYS')
    encrypter = Encrypter(json_secret_keys)
    return encrypter.encrypt(message_json)


def send_message_to_rabbitmq(message, tx_id, queue_name, encrypt=True):
    """
    Get details from environment credentials and send message to rabbitmq
    :param message: The message to send to the queue in JSON format
    :param tx_id: The transaction ID for the message
    :param queue_name: The rabbit queue to publish to
    :param encrypt: Flag whether message should be encrypted before publication
    :return: boolean
    """
    rabbitmq_amqp = current_app.config['RABBITMQ_AMQP']
    publisher = QueuePublisher([rabbitmq_amqp], queue_name)
    message = encrypt_message(message) if encrypt else message
    try:
        publisher.publish_message(message, headers={"tx_id": tx_id},
                                  immediate=False, mandatory=True)
        log.info('Message successfully sent to rabbitmq', tx_id=tx_id, queue=queue_name)
        return True
    except PublishMessageError:
        log.error('Message failed to send to rabbitmq', tx_id=tx_id)
        return False
