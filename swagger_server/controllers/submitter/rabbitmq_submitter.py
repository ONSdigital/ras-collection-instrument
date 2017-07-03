from ons_ras_common import ons_env

from pika import BlockingConnection, BasicProperties, URLParameters
from pika.exceptions import AMQPError


class RabbitMQSubmitter:

    def __init__(self):
        self.connection = None

    def send_message(self, message, queue, tx_id=None):
        """
        Sends a message to rabbit mq and returns a true or false depending on if it was successful
        :param message: The message to send to the rabbit mq queue
        :param queue: the name of the queue
        :param tx_id: transaction id
        :return: a boolean value indicating if it was successful
        """

        ons_env.logger.info('sending message to queue')

        properties = BasicProperties(headers={},
                                     delivery_mode=2)
        if tx_id:
            properties.headers['tx_id'] = tx_id

        try:
            self.connection = self._get_connection()
            channel = self.connection.channel()
            channel.queue_declare(queue=queue)
            published = channel.basic_publish(exchange='',
                                              routing_key=queue,
                                              body=message,
                                              properties=properties)
            return published
        except AMQPError:
            ons_env.logger.error("Rabbitmq message not sent")
            return False
        finally:
            if self.connection:
                self.connection.close()

    def _get_connection(self):
        rabbitmq_url = self._get_rabbitmq_url()
        return BlockingConnection(URLParameters(rabbitmq_url))

    @staticmethod
    def _get_rabbitmq_url():

        rabbitmq_url = "amqp://{username}:{password}@{host}:{port}/{vhost}" \
            .format(username=ons_env.rabbit.username,
                    password=ons_env.rabbit.password,
                    host=ons_env.rabbit.host,
                    port=ons_env.rabbit.port,
                    vhost=ons_env.rabbit.vhost)
        return rabbitmq_url
