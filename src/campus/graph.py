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
    is_bridge: bool = False  # 标记是否为桥梁
    congestion_factor: float = 0.0  # 拥塞系数（仅小桥使用）

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("Path length must be positive")
        if self.difficulty <= 0:
            raise ValueError("Difficulty must be positive")
        if self.capacity is not None and self.capacity <= 0:
            raise ValueError("Capacity must be positive when provided")

    def get_travel_time(self, base_speed: float = 80.0) -> float:
        """Calculate travel time (minutes) for this path.
        
        For bridges with limited capacity (small bridges), the travel time
        increases with congestion. Large bridges (capacity=None) have fixed time.
        """
        base_time = (self.length * self.difficulty) / base_speed
        
        # 如果是桥梁且有容量限制（小桥）
        if self.is_bridge and self.capacity is not None:
            # 计算当前占用率
            occupancy_ratio = len(self.current_students) / self.capacity
            # 动态成本：travel_time = base_time * (1 + congestion_factor * occupancy_ratio)
            # congestion_factor 控制拥塞影响程度，例如 1.0 表示满员时时间翻倍
            return base_time * (1.0 + self.congestion_factor * occupancy_ratio)
        
        # 普通路径或大桥（容量无限）：固定成本
        return base_time

    def has_capacity(self) -> bool:
        """Return True when the path can accept more students."""

        if self.capacity is None:
            return True
        return len(self.current_students) < self.capacity
    
    def get_congestion_level(self) -> str:
        """Return congestion level: 'clear', 'moderate', 'heavy', 'full'."""
        if not self.is_bridge or self.capacity is None:
            return 'clear'
        
        occupancy_ratio = len(self.current_students) / self.capacity
        if occupancy_ratio >= 1.0:
            return 'full'
        elif occupancy_ratio >= 0.7:
            return 'heavy'
        elif occupancy_ratio >= 0.4:
            return 'moderate'
        else:
            return 'clear'


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
        is_bridge: bool = False,
        congestion_factor: float = 1.0,
    ) -> Path:
        """Create a path between two buildings and return the forward edge.
        
        Args:
            is_bridge: Mark this path as a bridge (affects dynamic cost calculation)
            congestion_factor: How much congestion affects travel time (0-2.0 typical)
                              1.0 means full bridge doubles travel time
        """

        start = self._require_building(start_id)
        end = self._require_building(end_id)

        forward = Path(
            start=start, end=end, length=length, difficulty=difficulty, 
            capacity=capacity, is_bridge=is_bridge, congestion_factor=congestion_factor
        )
        start.add_path(forward)

        if bidirectional:
            backward = Path(
                start=end, end=start, length=length, difficulty=difficulty, 
                capacity=capacity, is_bridge=is_bridge, congestion_factor=congestion_factor
            )
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

    def find_second_shortest_path(self, start_id: str, end_id: str) -> float:
        """Find the cost of the second shortest path using Yen's algorithm (simplified version).
        
        Returns the total travel time of the second best route.
        Raises ValueError if no second path exists.
        """
        
        if start_id not in self.buildings or end_id not in self.buildings:
            raise ValueError("Start or end building does not exist")
        
        # First, find the shortest path
        try:
            best_cost, best_route = self.find_shortest_path(start_id, end_id)
        except ValueError:
            raise ValueError("No path exists")
        
        # If path has only 2 nodes, there's no alternative
        if len(best_route) <= 2:
            raise ValueError("No alternative path available")
        
        # Try to find alternative paths by temporarily removing each edge in the best path
        alternative_costs = []
        
        for i in range(len(best_route) - 1):
            # Temporarily mark this edge as having no capacity
            current_building = best_route[i]
            next_building = best_route[i + 1]
            
            # Find the path object to modify
            target_path = None
            for path in current_building.paths:
                if path.end.building_id == next_building.building_id:
                    target_path = path
                    break
            
            if target_path:
                # Save original capacity
                original_capacity = target_path.capacity
                original_students = target_path.current_students.copy()
                
                # Temporarily block this path
                target_path.capacity = 0
                target_path.current_students = ["__BLOCKED__"] * 1  # Make it full
                
                try:
                    # Try to find alternative route
                    alt_cost, _ = self.find_shortest_path(start_id, end_id)
                    if alt_cost > best_cost:  # Must be longer than best path
                        alternative_costs.append(alt_cost)
                except ValueError:
                    # No alternative route with this edge removed
                    pass
                
                # Restore original capacity
                target_path.capacity = original_capacity
                target_path.current_students = original_students
        
        if not alternative_costs:
            raise ValueError("No alternative path found")
        
        # Return the shortest among alternatives (which is the second shortest overall)
        return min(alternative_costs)

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
