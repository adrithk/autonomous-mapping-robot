"""Geometry and mission invariants; these do not establish runtime acceptance."""
from pathlib import Path
import sys
import unittest
import math
import numpy as np
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from my_bot_exploration.core import (Grid, frontiers, safe_mask, safe_at, Viewpoint,
                                     Exclusions, CompletionWindow, ActionGate, failure_kind)


class GeometryTests(unittest.TestCase):
    def room(self):
        data = np.full((50, 60), -1, dtype=int)
        data[4:46, 4:40] = 0
        data[4:46, 4] = 100
        data[4, 4:40] = 100
        data[45, 4:40] = 100
        return Grid(data, .05), Grid(np.zeros_like(data), .05)

    def test_ranked_viewpoints_are_known_and_clear(self):
        grid, costs = self.room()
        views, count = frontiers(grid, costs, (.8, 1.0))
        self.assertGreater(count, 0)
        self.assertTrue(views)
        self.assertEqual(views, frontiers(grid, costs, (.8, 1.0))[0])
        for v in views:
            self.assertTrue(safe_at(grid, costs, .22, v.x, v.y))
            self.assertEqual(grid.sample(v.x, v.y), 0)
            self.assertLess(v.x, 2.0-.22)

    def test_occupied_unknown_and_costmap_reject_viewpoints(self):
        grid, costs = self.room()
        costs.data[:] = 254
        self.assertFalse(frontiers(grid, costs, (.8, 1))[0])
        costs.data[:] = 255
        self.assertFalse(frontiers(grid, costs, (.8, 1))[0])
        self.assertFalse(safe_at(grid, costs, .22, -10, -10))

    def test_clearance_includes_cell_boundary(self):
        grid = Grid(np.zeros((20, 20), dtype=int), .1)
        grid.data[:, 5] = 100
        mask = safe_mask(grid, Grid(np.zeros((20, 20)), .1), .22)
        self.assertFalse(mask[10, 7])
        self.assertTrue(mask[10, 8])
        self.assertFalse(mask[0, 10])

    def test_noise_is_not_a_room_frontier(self):
        data = np.full((30, 30), 100)
        data[10, 10], data[10, 11] = 0, -1
        views, count = frontiers(Grid(data, .05), Grid(np.zeros_like(data), .05), (.5, .5))
        self.assertEqual((views, count), ([], 0))

    def test_fully_known_map_has_no_frontiers(self):
        grid = Grid(np.zeros((30, 30)), .05)
        self.assertEqual(frontiers(grid, grid, (.5, .5)), ([], 0))

    def test_world_coordinates_survive_map_growth(self):
        grid, costs = self.room()
        views, _ = frontiers(grid, costs, (.8, 1))
        padded = Grid(np.pad(grid.data, 10, constant_values=-1), .05, -.5, -.5)
        grown_costs = Grid(np.zeros(padded.data.shape), .05, -.5, -.5)
        grown, _ = frontiers(padded, grown_costs, (.8, 1))
        for a, b in zip(views, grown):
            self.assertAlmostEqual(a.x, b.x)
            self.assertAlmostEqual(a.y, b.y)
            self.assertEqual(a.signature, b.signature)

    def test_rotated_map_origin_and_different_costmap_resolution(self):
        grid = Grid(np.zeros((40, 40)), .05, 3, -2, math.pi/2)
        x, y = grid.world(10, 15)
        self.assertEqual(tuple(map(int, grid.cells(x, y))), (10, 15))
        costs = Grid(np.zeros((100, 100)), .1, -1, -3)
        self.assertTrue(safe_at(grid, costs, .22, float(x), float(y)))

    def test_failed_candidate_retries_then_waits_for_local_change(self):
        grid, _ = self.room()
        view = Viewpoint(1, 1, 0, 1, 1, 1, grid.fingerprint(1, 1))
        cache = Exclusions(30)
        cache.add(view, 0)
        self.assertTrue(cache.blocked(view, 1, grid))
        self.assertTrue(cache.waiting_retry(1))
        self.assertFalse(cache.blocked(view, 31, grid))
        cache.add(view, 31)
        self.assertTrue(cache.blocked(view, 100, grid))
        self.assertFalse(cache.waiting_retry(100))
        grid.data[20, 20] = 10
        self.assertTrue(cache.blocked(view, 101, grid))
        grid.data[20, 20] = 100
        self.assertFalse(cache.blocked(view, 101, grid))


class PolicyTests(unittest.TestCase):
    def test_completion_needs_distinct_updates_and_time(self):
        w = CompletionWindow()
        self.assertFalse(w.observe('COMPLETE', 1, 0))
        self.assertFalse(w.observe('COMPLETE', 1, 20))
        self.assertFalse(w.observe('COMPLETE', 2, 21))
        self.assertTrue(w.observe('COMPLETE', 3, 22))
        self.assertFalse(w.observe(None, 4, 23))
        self.assertFalse(w.observe('COMPLETE', 5, 24))

    def test_partial_is_never_promoted_to_complete(self):
        w = CompletionWindow()
        for sequence, now in [(1, 0), (2, 3), (3, 6)]:
            ready = w.observe('PARTIAL', sequence, now)
        self.assertTrue(ready)
        self.assertEqual(w.kind, 'PARTIAL')
        self.assertFalse(w.observe('COMPLETE', 4, 7))

    def test_stop_before_acceptance_holds_single_action_lease(self):
        gate = ActionGate()
        ticket = gate.begin()
        gate.stop()
        self.assertTrue(gate.current(ticket))
        with self.assertRaises(RuntimeError):
            gate.begin()
        self.assertFalse(gate.finish(ticket))  # cancelled callback cannot dispatch navigation
        second = gate.begin()
        self.assertFalse(gate.finish(ticket))  # stale callback cannot clear new goal
        self.assertTrue(gate.current(second))
        self.assertTrue(gate.finish(second))

    def test_action_failures_do_not_hide_tf_faults(self):
        self.assertEqual(failure_kind(4, 0), 'success')
        self.assertEqual(failure_kind(6, 208, True), 'blocked')
        self.assertEqual(failure_kind(6, 202, True), 'fault')
        self.assertEqual(failure_kind(6, 102), 'fault')
        self.assertEqual(failure_kind(6, 105), 'blocked')
        self.assertEqual(failure_kind(6, 702), 'fault')
        self.assertEqual(failure_kind(6, 0), 'fault')

    def test_config_clearance_and_exclusive_rviz(self):
        root = Path(__file__).resolve().parents[1]
        p = yaml.safe_load((root/'config/exploration.yaml').read_text())['exploration_manager']['ros__parameters']
        nav = yaml.safe_load((root/'config/nav2.yaml').read_text())
        cost = nav['global_costmap']['global_costmap']['ros__parameters']
        self.assertGreaterEqual(p['robot_radius'], cost['robot_radius']+cost['footprint_padding'])
        rviz = yaml.safe_load((root/'config/exploration.rviz').read_text())
        self.assertNotIn('nav2_rviz_plugins/GoalTool', [v['Class'] for v in rviz['Visualization Manager']['Tools']])
        self.assertIn('rviz_default_plugins/MarkerArray', [v['Class'] for v in rviz['Visualization Manager']['Displays']])

class SyntheticExplorationTests(unittest.TestCase):
    def test_successive_views_reveal_occluded_area(self):
        # A deterministic geometric fixture, not Gazebo, wheel dynamics or SLAM.
        from scipy import ndimage
        truth = np.zeros((45, 65), dtype=int)
        truth[[0, -1], :] = 100
        truth[:, [0, -1]] = 100
        truth[:34, 32] = 100  # doorway above the partition
        known = np.full_like(truth, -1)
        grid, costs = Grid(known, .1), Grid(np.zeros_like(truth), .1)
        robot = (1.2, 1.2)
        cache = Exclusions(1)

        def observe(position):
            for angle in np.linspace(-math.pi, math.pi, 1440, endpoint=False):
                for distance in np.arange(0, 3.0, .04):
                    r, c = map(int, grid.cells(position[0]+distance*math.cos(angle), position[1]+distance*math.sin(angle)))
                    if not (0 <= r < truth.shape[0] and 0 <= c < truth.shape[1]):
                        break
                    known[r, c] = truth[r, c]
                    if truth[r, c] == 100:
                        break
        observe(robot)
        initial = np.count_nonzero(known >= 0)
        visited = 0
        for step in range(45):
            views, _ = frontiers(grid, costs, robot)
            safe = safe_mask(grid, costs, .22)
            components, _ = ndimage.label(safe)
            r, c = map(int, grid.cells(*robot))
            component = components[r, c]
            choices = [v for v in views if not cache.blocked(v, step*2, grid)]
            selected = None
            for v in choices:
                vr, vc = map(int, grid.cells(v.x, v.y))
                if component and components[vr, vc] == component:
                    selected = v
                    break
                cache.add(v, step*2)
            if selected is None:
                break
            cache.add(selected, step*2)
            robot = (selected.x, selected.y)
            visited += 1
            observe(robot)
        self.assertGreaterEqual(visited, 2)
        self.assertGreater(np.count_nonzero(known >= 0), initial+200)
        self.assertGreater(np.count_nonzero(known[:, 34:] >= 0), 500)


if __name__ == "__main__":
    unittest.main()
