import unittest
from unittest.mock import Mock, MagicMock

from cfenv import Service

from application.cloud.cloudfoundry import ONSCloudFoundry


class TestONSCloudFoundry(unittest.TestCase):

    def test_get_queue(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = 'service'

        queue = cf.queue

        self.assertEqual(queue, 'service')

    def test_no_queue_bound(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.side_effect = StopIteration()

        queue = cf.queue

        self.assertIsNone(queue)

    def test_get_rm_queue_from_cloudfoundry(self):
        cf = ONSCloudFoundry()
        cf._cf_env = MagicMock()
        cf._cf_env.get_service.return_value = Service({'credentials': {'uri': 'service'}})

        queue = cf.rm_queue_uri

        self.assertEqual(queue, 'service')
        cf._cf_env.get_service.assert_called_with(name='rm-rabbitmq')

    def test_no_rm_queue_bound_uses_environmental_variable(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = None

        queue = cf.rm_queue_uri

        self.assertEqual('rabbit_amqp', queue)

    def test_get_sdx_queue_from_cloudfoundry(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = Service({'credentials': {'uri': 'service'}})

        queue = cf.sdx_queue_uri

        self.assertEqual(queue, 'service')
        cf._cf_env.get_service.assert_called_with(name='sdx-rabbitmq')

    def test_no_sdx_queue_bound_uses_environmental_variable(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = None

        queue = cf.sdx_queue_uri

        self.assertEqual('rabbit_amqp', queue)

    def test_get_db_from_cloudfoundry(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = Service({'credentials': {'uri': 'service'}})

        queue = cf.db_uri

        self.assertEqual(queue, 'service')
        cf._cf_env.get_service.assert_called_with(name='ras-ci-db')

    def test_no_db_bound_uses_environmental_variable(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = None

        queue = cf.db_uri

        self.assertEqual('postgres://postgres:postgres@localhost:6432/postgres', queue)
