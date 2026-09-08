"""No ROS installation required to check keyboard motion and expiry."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('teleop_wasd', Path(__file__).resolve().parents[1]/'scripts/teleop_wasd.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TeleopTests(unittest.TestCase):
    def test_mapping_and_stop(self):
        command = module.KeyboardCommand()
        for key, motion in [('w', (0.1, 0)), ('s', (-0.1, 0)),
                            ('a', (0, 0.5)), ('d', (0, -0.5)),
                            ('x', (0, 0)), (' ', (0, 0)), ('?', (0, 0))]:
            command.key(key, 1)
            self.assertEqual(command.value(1.1), motion)

    def test_expiry_and_repeat(self):
        command = module.KeyboardCommand()
        self.assertEqual(command.value(0), (0, 0))
        command.key('w', 1)
        self.assertEqual(command.value(1.2), (0, 0))
        command.key('w', 2)
        command.key('w', 2.1)
        self.assertEqual(command.value(2.25), (0.1, 0))
        self.assertEqual(command.value(2.31), (0, 0))
        command.key('a', 3)
        self.assertEqual(command.value(3.1), (0, 0.5))

    def test_invalid_speed(self):
        for value in [0, -1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                module.KeyboardCommand(speed=value)
            with self.assertRaises(ValueError):
                module.KeyboardCommand(turn=value)


if __name__ == '__main__':
    unittest.main()
