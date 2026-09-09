"""Deterministic map geometry and mission guards; no ROS or actuator access."""
from dataclasses import dataclass
import hashlib
import math
import numpy as np
from scipy import ndimage


@dataclass
class Grid:
    data: np.ndarray
    resolution: float
    x: float = 0.0
    y: float = 0.0
    yaw: float = 0.0

    def __post_init__(self):
        self.data = np.asarray(self.data)
        if (self.data.ndim != 2 or 0 in self.data.shape or
                not all(math.isfinite(v) for v in (self.resolution, self.x, self.y, self.yaw))
                or self.resolution <= 0):
            raise ValueError('Invalid grid geometry')

    def world(self, rows, cols):
        lx, ly = (np.asarray(cols)+.5)*self.resolution, (np.asarray(rows)+.5)*self.resolution
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return self.x+c*lx-s*ly, self.y+s*lx+c*ly

    def cells(self, x, y):
        dx, dy = np.asarray(x)-self.x, np.asarray(y)-self.y
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return (np.floor((-s*dx+c*dy)/self.resolution).astype(int),
                np.floor((c*dx+s*dy)/self.resolution).astype(int))

    def sample(self, x, y, outside=-1):
        rows, cols = self.cells(x, y)
        valid = (rows >= 0) & (cols >= 0) & (rows < self.data.shape[0]) & (cols < self.data.shape[1])
        return np.where(valid, self.data[np.clip(rows, 0, self.data.shape[0]-1),
                                        np.clip(cols, 0, self.data.shape[1]-1)], outside)

    def fingerprint(self, x, y):
        # World-anchored samples survive map resizing / an origin shift.
        steps = math.ceil(.8/self.resolution)
        offsets = np.arange(-steps, steps+1)*self.resolution
        dx, dy = np.meshgrid(offsets, offsets)
        # Sample at world-grid cell centers to avoid floating boundary ambiguity.
        cx = (math.floor(x/self.resolution)+.5)*self.resolution
        cy = (math.floor(y/self.resolution)+.5)*self.resolution
        values = self.sample(cx+dx, cy+dy)
        # Only occupancy-class changes justify retrying; probability jitter does not.
        classes = np.where(values < 0, 0, np.where(values <= 25, 1, 2)).astype(np.uint8)
        return hashlib.sha256(classes.tobytes()).hexdigest()


@dataclass(frozen=True)
class Viewpoint:
    x: float
    y: float
    yaw: float
    anchor_x: float
    anchor_y: float
    score: float
    signature: str


def safe_mask(grid, costmap, radius):
    free = (grid.data >= 0) & (grid.data <= 25)
    # Padding treats out-of-map space as unknown. Subtract a cell half-diagonal
    # because EDT measures cell centers, not the nearest occupied-cell boundary.
    clearance = ndimage.distance_transform_edt(np.pad(free, 1))[1:-1, 1:-1]*grid.resolution
    safe = free & (clearance >= radius + grid.resolution/math.sqrt(2))
    rows, cols = np.indices(grid.data.shape)
    x, y = grid.world(rows, cols)
    costs = costmap.sample(x, y, outside=255)
    return safe & (costs >= 0) & (costs < 253)


def safe_at(grid, costmap, radius, x, y):
    rows, cols = grid.cells(x, y)
    if not (0 <= rows < grid.data.shape[0] and 0 <= cols < grid.data.shape[1]):
        return False
    return bool(safe_mask(grid, costmap, radius)[rows, cols])


def frontiers(grid, costmap, robot, radius=.22, minimum_size=.15, view_distance=.8):
    """Return ranked safe viewpoints and count of non-noise frontier clusters.

    Candidates are checked against the SLAM grid and raw Nav2 costmap. Reachability
    is deliberately delegated to Nav2 rather than duplicating its path planner.
    """
    free = (grid.data >= 0) & (grid.data <= 25)
    edge = free & ndimage.binary_dilation(grid.data < 0, structure=ndimage.generate_binary_structure(2, 1))
    labels, _ = ndimage.label(edge, structure=np.ones((3, 3)))
    safe = safe_mask(grid, costmap, radius)
    candidates, count = [], 0
    for label_id, bounds in enumerate(ndimage.find_objects(labels), start=1):
        if bounds is None:
            continue
        cluster_rows, cluster_cols = np.where(labels[bounds] == label_id)
        if len(cluster_rows)*grid.resolution + 1e-9 < minimum_size:
            continue
        count += 1
        cluster_rows += bounds[0].start
        cluster_cols += bounds[1].start
        # Choose an actual frontier cell near the centroid, never a centroid in a wall.
        index = np.argmin((cluster_rows-cluster_rows.mean())**2+(cluster_cols-cluster_cols.mean())**2)
        # Long/L-shaped frontiers need alternatives away from an obstructed centroid.
        anchor_indices = sorted(set((int(index), 0, len(cluster_rows)-1)))
        for anchor_index in anchor_indices:
            ar, ac = cluster_rows[anchor_index], cluster_cols[anchor_index]
            ax, ay = map(float, grid.world(ar, ac))
            pad = math.ceil(view_distance/grid.resolution)
            r0, r1 = max(0, ar-pad), min(grid.data.shape[0], ar+pad+1)
            c0, c1 = max(0, ac-pad), min(grid.data.shape[1], ac+pad+1)
            rr, cc = np.where(safe[r0:r1, c0:c1])
            rr, cc = rr+r0, cc+c0
            x, y = grid.world(rr, cc)
            distances = np.hypot(x-ax, y-ay)
            travel = np.hypot(x-robot[0], y-robot[1])
            order = np.lexsort((cc, rr, travel + distances))
            selected = []
            for i in order:
                if distances[i] > view_distance or any(math.hypot(x[i]-sx, y[i]-sy) < .25 for sx, sy in selected):
                    continue
                # The viewpoint must see the frontier through known free space.
                n = max(2, math.ceil(distances[i]/(grid.resolution*.5)))
                ray = grid.sample(np.linspace(x[i], ax, n), np.linspace(y[i], ay, n))
                if np.any((ray < 0) | (ray > 25)):
                    continue
                selected.append((x[i], y[i]))
                gain = len(cluster_rows)*grid.resolution
                candidates.append(Viewpoint(float(x[i]), float(y[i]), math.atan2(ay-y[i], ax-x[i]),
                                            ax, ay, gain/(.5+travel[i]), grid.fingerprint(ax, ay)))
                if len(selected) == 3:
                    break
    candidates.sort(key=lambda v: (-v.score, v.x, v.y))
    return candidates, count


class Exclusions:
    """Temporary failures; local map change permits immediate reconsideration."""
    def __init__(self, cooldown=30.0):
        self.cooldown = cooldown
        self.entries = []

    def add(self, view, now):
        previous = [(v, t, n) for v, t, n in self.entries
                    if math.hypot(v.x-view.x, v.y-view.y) < .2 and v.signature == view.signature]
        attempts = max((n for _, _, n in previous), default=0)+1
        self.entries = [(v, t, n) for v, t, n in self.entries
                        if math.hypot(v.x-view.x, v.y-view.y) >= .2]
        self.entries.append((view, now, attempts))

    def blocked(self, view, now, grid):
        self.entries = [(v, t, n) for v, t, n in self.entries
                        if grid.fingerprint(v.anchor_x, v.anchor_y) == v.signature]
        return any(math.hypot(v.x-view.x, v.y-view.y) < .2 and
                   (attempts >= 2 or now-t < self.cooldown)
                   for v, t, attempts in self.entries)

    def waiting_retry(self, now):
        return any(attempts < 2 and now-t < self.cooldown for _, t, attempts in self.entries)


class CompletionWindow:
    def __init__(self, seconds=5.0, updates=3):
        self.seconds, self.updates = seconds, updates
        self.reset()

    def reset(self):
        self.kind, self.first, self.sequence, self.count = None, None, None, 0

    def observe(self, kind, sequence, now):
        if kind is None:
            self.reset()
            return False
        if kind != self.kind:
            self.reset()
            self.kind, self.first = kind, now
        if sequence != self.sequence:
            self.sequence, self.count = sequence, self.count+1
        return self.count >= self.updates and now-self.first >= self.seconds


class ActionGate:
    """One action lease, retained through pending acceptance AND cancellation."""
    def __init__(self):
        self.serial, self.ticket, self.cancel = 0, None, False

    def begin(self):
        if self.ticket is not None:
            raise RuntimeError('Action still outstanding')
        self.serial += 1
        self.ticket, self.cancel = self.serial, False
        return self.ticket

    def stop(self):
        self.cancel = True

    def current(self, ticket):
        return self.ticket == ticket

    def finish(self, ticket):
        if not self.current(ticket):
            return False
        deliver = not self.cancel
        self.ticket = None
        return deliver


def failure_kind(status, error_code, planning=False):
    if status == 4 and error_code == 0:  # action_msgs/GoalStatus.STATUS_SUCCEEDED
        return 'success'
    # Jazzy FollowPath uses 100-series codes; planner uses 200-series codes.
    # Only documented spatial/progress failures may exclude a viewpoint. Unknown
    # errors (including recovery TF errors) fault rather than masquerade as coverage.
    blocked = {204, 206, 208} if planning else {104, 105, 106, 204, 206, 208, 703}
    return 'blocked' if error_code in blocked else 'fault'
