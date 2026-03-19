import unittest
from unittest.mock import patch, MagicMock
import sys

class TestGetTasksClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Define the mocks
        cls.mocks = {
            'fastapi': MagicMock(),
            'pydantic': MagicMock(),
            'google.cloud': MagicMock(),
            'google.cloud.tasks_v2': MagicMock(),
            'app.gcs': MagicMock(),
            'app.analysis': MagicMock(),
        }

        # Use patch.dict to temporarily update sys.modules
        cls.patcher = patch.dict('sys.modules', cls.mocks)
        cls.patcher.start()

        # Import app.main after mocking dependencies
        import app.main
        cls.app_main = app.main

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def setUp(self):
        # Clear the lru_cache for get_tasks_client
        self.app_main.get_tasks_client.cache_clear()

    def test_get_tasks_client_creates_client(self):
        # Arrange
        with patch('app.main.tasks_v2.CloudTasksClient') as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance

            # Act
            client = self.app_main.get_tasks_client()

            # Assert
            mock_client_class.assert_called_once()
            self.assertEqual(client, mock_instance)

    def test_get_tasks_client_is_cached(self):
        # Arrange
        with patch('app.main.tasks_v2.CloudTasksClient') as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance

            # Act
            client1 = self.app_main.get_tasks_client()
            client2 = self.app_main.get_tasks_client()

            # Assert
            mock_client_class.assert_called_once()
            self.assertEqual(client1, mock_instance)
            self.assertEqual(client2, mock_instance)
            self.assertEqual(client1, client2)

if __name__ == '__main__':
    unittest.main()
