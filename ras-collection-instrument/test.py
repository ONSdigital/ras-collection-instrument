import unittest

from app import app

ok = 200
unauthorized = 401


class ComponentTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_something(self):
        # Given
        # Some preconditions

        # When
        # We take an action

        # Then
        # We should get some verifiable results

        pass


if __name__ == '__main__':
    unittest.main()
