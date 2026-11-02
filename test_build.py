import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent

class BuildTests(unittest.TestCase):
    def test_missing_input_clears_previous_ready_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            report = output / 'build-report.json'
            report.write_text('{"ready_for_delivery": true}')
            result = subprocess.run([sys.executable, str(BASE / 'build.py'),
                                     '--data', str(output / 'missing.json'),
                                     '--output-dir', str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(report.read_text())['ready_for_delivery'])

if __name__ == '__main__':
    unittest.main()
