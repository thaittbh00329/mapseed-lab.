"""Reference generator and invariant checks for four-neighbor tile maps."""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from random import Random

MIN_SIDE = 7
MAX_SIDE = 24
TILES = frozenset("#.SE")
WALKABLE = frozenset(".SE")


@dataclass(frozen=True)
class Case:
    seed: int
    width: int
    height: int
    density: int

    def __post_init__(self):
        if not MIN_SIDE <= self.width <= MAX_SIDE or not MIN_SIDE <= self.height <= MAX_SIDE:
            raise ValueError(f"width and height must be between {MIN_SIDE} and {MAX_SIDE}")
        if not 0 <= self.density <= 100:
            raise ValueError("wall density must be between 0 and 100")


def generate(case: Case) -> list[str]:
    rng = Random(case.seed)
    width, height = case.width, case.height
    grid = [["#"] * width for _ in range(height)]
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            grid[y][x] = "#" if rng.randrange(100) < case.density else "."

    steps = [(1, 0)] * (width - 3) + [(0, 1)] * (height - 3)
    rng.shuffle(steps)
    x = y = 1
    for dx, dy in steps:
        x, y = x + dx, y + dy
        grid[y][x] = "."
    grid[1][1] = "S"
    grid[height - 2][width - 2] = "E"
    return ["".join(row) for row in grid]


def reachable(grid: Sequence[str], start: tuple[int, int], end: tuple[int, int]) -> bool:
    queue = deque([start])
    visited = {start}
    while queue:
        x, y = queue.popleft()
        if (x, y) == end:
            return True
        for cell in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            nx, ny = cell
            if (0 <= ny < len(grid) and 0 <= nx < len(grid[0])
                    and cell not in visited and grid[ny][nx] in WALKABLE):
                visited.add(cell)
                queue.append(cell)
    return False


def validate(grid: Sequence[str]) -> tuple[str, ...]:
    """Return violation codes in a stable order."""
    if (isinstance(grid, (str, bytes)) or not grid
            or not all(isinstance(row, str) for row in grid)
            or not grid[0] or any(len(row) != len(grid[0]) for row in grid)):
        return ("shape",)

    issues = []
    if any(tile not in TILES for row in grid for tile in row):
        issues.append("tile")
    if (set(grid[0]) != {"#"} or set(grid[-1]) != {"#"}
            or any(row[0] != "#" or row[-1] != "#" for row in grid)):
        issues.append("border")
    starts = []
    exits = []
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == "S":
                starts.append((x, y))
            elif tile == "E":
                exits.append((x, y))
    if len(starts) != 1:
        issues.append("spawn")
    if len(exits) != 1:
        issues.append("exit")
    if len(starts) == 1 and len(exits) == 1 and not reachable(grid, starts[0], exits[0]):
        issues.append("route")
    return tuple(issues)
