import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_health(self):
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
