import unittest
from unittest.mock import patch

from pika.exceptions import AMQPError
from application.exceptions import RasError
from application.controllers.rabbitmq_submitter import RabbitMQSubmitter

TEST_FILE_LOCATION = 'tests/files/tests.xlsx'


class TestRabbitMQSubmitter(unittest.TestCase):
    """ Rabbitmq unit tests"""

    def mock_get_rabbitmq_url(self):
        pass

    def test_when_message_sent_then_published_true(self):

        # Given a mocked rabbitmq
        with patch('application.controllers.rabbitmq_submitter.BlockingConnection'), \
             patch('application.controllers.rabbitmq_submitter.URLParameters'):
            rabbitmq_submitter = RabbitMQSubmitter('tests-connection')
            rabbitmq_submitter._get_rabbitmq_url = self.mock_get_rabbitmq_url

            # When a message is send
            published = rabbitmq_submitter.send_message(message={}, queue='Seft.Responses', tx_id='tests')

            # Then it is published successfully
            self.assertTrue(published)

    def test_connection_failure(self):

        # Given a mocked rabbitmq
        with patch('application.controllers.rabbitmq_submitter.BlockingConnection') as connection, \
             patch('application.controllers.rabbitmq_submitter.URLParameters'):

            # When a Error is generated on a connection
            connection.side_effect = AMQPError()
            rabbitmq_submitter = RabbitMQSubmitter('tests-connection')
            rabbitmq_submitter._get_rabbitmq_url = self.mock_get_rabbitmq_url

            # Then an upload exception is raised
            with self.assertRaises(RasError):
                rabbitmq_submitter.send_message(message={}, queue='Seft.Responses', tx_id='tests')
