import unittest
from unittest.mock import Mock

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


