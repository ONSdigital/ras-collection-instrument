from unittest.mock import patch, mock_open

from tests.test_client import TestClient


class TestInfoView(TestClient):
    """Info view unit tests"""

    def test_info(self):

        # Given the application is running and the git path is mocked
        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data='{"origin": "test"}')
        ):
            # When a call to the info end point is made
            response = self.client.get("/info")

            # Then it returns details from git and the app
            self.assertIn("origin", response.data.decode())
            self.assertIn("name", response.data.decode())
            self.assertIn("version", response.data.decode())
