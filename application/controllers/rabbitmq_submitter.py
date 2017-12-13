from pika import BlockingConnection, BasicProperties, URLParameters
from pika.exceptions import AMQPError
from application.exceptions import RasError
from structlog import get_logger

log = get_logger()


class RabbitMQSubmitter:

    def __init__(self, uri):
        self.uri = uri
        self.connection = None

    def send_message(self, message, queue, tx_id=None):
        """
        Sends a message to rabbit mq and returns a true or false depending on if it was successful
        :param message: The message to send to the rabbit mq queue
        :param queue: the name of the queue
        :param tx_id: transaction id
        :return: boolean
        """

        log.info('Sending message to queue')

        properties = BasicProperties(headers={},
                                     delivery_mode=2)
        if tx_id:
            properties.headers['tx_id'] = tx_id

        try:
            self.connection = BlockingConnection(URLParameters(self.uri))
            channel = self.connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            published = channel.basic_publish(exchange='',
                                              routing_key=queue,
                                              body=message,
                                              properties=properties)

        except AMQPError:
            raise RasError('Rabbitmq AMQP error', 500)
        finally:
            if self.connection:
                self.connection.close()
        return published
