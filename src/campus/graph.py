"""Core graph data structures for the campus simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from math import inf
from typing import Dict, List, Optional, Tuple


@dataclass
class Building:
    """Represents a single location node on the campus map."""

    building_id: str
    name: str
    x: int
    y: int
    paths: List["Path"] = field(default_factory=list)

    def add_path(self, path: "Path") -> None:
        """Register an outgoing path from this building."""

        self.paths.append(path)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Building(id={self.building_id!r}, name={self.name!r})"


@dataclass
class Path:
    """Represents a traversal edge between two buildings."""

    start: Building
    end: Building
    length: float
    difficulty: float = 1.0
    capacity: Optional[int] = None
    current_students: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("Path length must be positive")
        if self.difficulty <= 0:
            raise ValueError("Difficulty must be positive")
        if self.capacity is not None and self.capacity <= 0:
            raise ValueError("Capacity must be positive when provided")

    def get_travel_time(self, base_speed: float = 80.0) -> float:
        """Calculate travel time (minutes) for this path."""

        return (self.length * self.difficulty) / base_speed

    def has_capacity(self) -> bool:
        """Return True when the path can accept more students."""

        if self.capacity is None:
            return True
        return len(self.current_students) < self.capacity


class Graph:
    """Manages the campus graph and shortest path queries."""

    def __init__(self) -> None:
        self.buildings: Dict[str, Building] = {}

    def add_building(self, building: Building) -> None:
        """Add a building node to the graph."""

        if building.building_id in self.buildings:
            raise ValueError(f"Building {building.building_id} already exists")
        self.buildings[building.building_id] = building

    def connect_buildings(
        self,
        start_id: str,
        end_id: str,
        length: float,
        *,
        difficulty: float = 1.0,
        capacity: Optional[int] = None,
        bidirectional: bool = True,
    ) -> Path:
        """Create a path between two buildings and return the forward edge."""

        start = self._require_building(start_id)
        end = self._require_building(end_id)

        forward = Path(start=start, end=end, length=length, difficulty=difficulty, capacity=capacity)
        start.add_path(forward)

        if bidirectional:
            backward = Path(start=end, end=start, length=length, difficulty=difficulty, capacity=capacity)
            end.add_path(backward)

        return forward

    def find_shortest_path(self, start_id: str, end_id: str) -> Tuple[float, List[Building]]:
        """Run Dijkstra to find the lowest travel-time route."""

        if start_id not in self.buildings or end_id not in self.buildings:
            raise ValueError("Start or end building does not exist")

        distances: Dict[str, float] = {start_id: 0.0}
        previous: Dict[str, str] = {}
        heap: List[Tuple[float, str]] = [(0.0, start_id)]
        visited: set[str] = set()

        while heap:
            current_time, current_id = heappop(heap)
            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id == end_id:
                break

            current_building = self.buildings[current_id]
            for path in current_building.paths:
                if not path.has_capacity():
                    continue
                neighbor_id = path.end.building_id
                if neighbor_id in visited:
                    continue

                new_time = current_time + path.get_travel_time()
                if new_time < distances.get(neighbor_id, inf):
                    distances[neighbor_id] = new_time
                    previous[neighbor_id] = current_id
                    heappush(heap, (new_time, neighbor_id))

        if end_id not in distances:
            raise ValueError(f"No path found from {start_id} to {end_id}")

        return distances[end_id], self._reconstruct_route(previous, start_id, end_id)

    def _reconstruct_route(
        self,
        previous: Dict[str, str],
        start_id: str,
        end_id: str,
    ) -> List[Building]:
        route: List[Building] = []
        current_id = end_id
        while True:
            route.append(self.buildings[current_id])
            if current_id == start_id:
                break
            current_id = previous[current_id]
        route.reverse()
        return route

    def _require_building(self, building_id: str) -> Building:
        if building_id not in self.buildings:
            raise ValueError(f"Building {building_id} not found")
        return self.buildings[building_id]

    def get_path(self, start_id: str, end_id: str) -> Path:
        """Return the direct path object between two buildings."""

        start = self._require_building(start_id)
        for path in start.paths:
            if path.end.building_id == end_id:
                return path
        raise ValueError(f"Path from {start_id} to {end_id} not found")

    def get_building(self, building_id: str) -> Building:
        """Return the building identified by ``building_id``."""

        return self._require_building(building_id)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Graph(buildings={list(self.buildings)})"
