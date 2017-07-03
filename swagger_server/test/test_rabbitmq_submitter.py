import unittest

from unittest.mock import patch

from pika.exceptions import AMQPError

from swagger_server.controllers.submitter.rabbitmq_submitter import RabbitMQSubmitter


TEST_FILE_LOCATION = 'swagger_server/test/test.xlsx'


class TestRabbitMQSubmitter(unittest.TestCase):
    """ Rabbitmq unit tests"""

    def mock_get_rabbitmq_url(self):
        pass

    def test_when_message_sent_then_published_true(self):

        # Given a mocked rabbitmq
        with patch('swagger_server.controllers.submitter.rabbitmq_submitter.BlockingConnection'), \
             patch('swagger_server.controllers.submitter.rabbitmq_submitter.URLParameters'):
            rabbitmq_submitter = RabbitMQSubmitter()
            rabbitmq_submitter._get_rabbitmq_url = self.mock_get_rabbitmq_url

            # When a message is send
            published = rabbitmq_submitter.send_message(message={}, queue='Seft.Responses', tx_id='test')

            # Then it is published successfully
            self.assertTrue(published)

    def test_when_message_sent_then_published_fasle(self):

        # Given a mocked rabbitmq
        with patch('swagger_server.controllers.submitter.rabbitmq_submitter.BlockingConnection') as connection, \
             patch('swagger_server.controllers.submitter.rabbitmq_submitter.URLParameters'):

            # When a Error is generated on a connection
            connection.side_effect = AMQPError()
            rabbitmq_submitter = RabbitMQSubmitter()
            rabbitmq_submitter._get_rabbitmq_url = self.mock_get_rabbitmq_url
            published = rabbitmq_submitter.send_message(message={}, queue='Seft.Responses', tx_id='test')

            # Then a message is not sent
            self.assertFalse(published)
