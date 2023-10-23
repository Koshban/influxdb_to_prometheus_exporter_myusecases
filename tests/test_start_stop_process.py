import unittest
from unittest.mock import patch, call
import subprocess
from src.query_and_json import start 

class TestStartStop(unittest.TestCase):
    @patch('subprocess.run')
    def test_start_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(args='mock command', returncode=0)
        
        result = start()
        
        mock_run.assert_called_once_with('mock command', check=True, shell=True, capture_output=True)
        self.assertEqual(result, 0)

    @patch('subprocess.run')
    def test_start_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'mock command')
        
        result = start()
        
        mock_run.assert_called_once_with('mock command', check=True, shell=True, capture_output=True)
        self.assertEqual(result, 1)  


if __name__ == '__main__':
    unittest.main()