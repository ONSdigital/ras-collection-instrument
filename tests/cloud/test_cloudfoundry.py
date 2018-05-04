import unittest
from unittest.mock import Mock

from application.cloud.cloudfoundry import ONSCloudFoundry


class TestONSCloudFoundry(unittest.TestCase):

    def test_get_rm_queue_from_cloudfoundry(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = 'service'

        queue = cf.rm_queue

        self.assertEqual(queue, 'service')

    def test_no_rm_queue_bound_uses_environmental_variable(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.side_effect = StopIteration()

        queue = cf.rm_queue

        self.assertEqual('rabbit_amqp', queue)

    def test_get_sdx_queue_from_cloudfoundry(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.return_value = 'service'

        queue = cf.sdx_queue

        self.assertEqual(queue, 'service')

    def test_no_sdx_queue_bound_uses_environmental_variable(self):
        cf = ONSCloudFoundry()
        cf._cf_env = Mock()
        cf._cf_env.get_service.side_effect = StopIteration()

        queue = cf.sdx_queue

        self.assertEqual('rabbit_amqp', queue)
