"""
Module for python unit tests
"""
import unittest

from app import app


class ComponentTestCase(unittest.TestCase):
    """
    The component test case
    """
    def setUp(self):
        """
        Initial setup for test class
        """
        self.app = app.test_client()

    def tearDown(self):
        """
        Overriding default tearDown method
        :return:
        """
        pass

    def test_something(self):
        """
        Method that tests something
        """
        # Given
        # Some preconditions

        # When
        # We take an action

        # Then
        # We should get some verifiable results

        pass


if __name__ == '__main__':
    unittest.main()
