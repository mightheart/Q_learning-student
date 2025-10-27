"""Core graph data structures for the campus simulation."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
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
    is_bridge: bool = False
    congestion_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("Path length must be positive")
        if self.difficulty <= 0:
            raise ValueError("Difficulty must be positive")
        if self.capacity is not None and self.capacity <= 0:
            raise ValueError("Capacity must be positive when provided")

    def get_travel_time(self, base_speed: float = 80.0) -> float:
        """
        计算此路径的通行时间（分钟）。
        对于有容量限制的桥梁，通行时间会随着拥塞而增加。
        """
        base_time = (self.length * self.difficulty) / base_speed
        
        if self.is_bridge and self.capacity is not None and self.capacity > 0:
            occupancy_ratio = len(self.current_students) / self.capacity
            return base_time * (1.0 + self.congestion_factor * occupancy_ratio)
        
        return base_time

    def has_capacity(self) -> bool:
        """如果路径还能容纳更多学生，则返回True。"""
        if self.capacity is None:
            return True
        return len(self.current_students) < self.capacity


class Graph:
    """管理校园图结构。"""

    def __init__(self) -> None:
        self.buildings: Dict[str, Building] = {}
        self._distance_matrix: Optional[Dict[str, Dict[str, float]]] = None

    def add_building(self, building: Building) -> None:
        """向图中添加一个建筑节点。"""
        if building.building_id in self.buildings:
            raise ValueError(f"Building {building.building_id} already exists")
        self.buildings[building.building_id] = building
        self._distance_matrix = None # 添加新建筑后，距离缓存失效

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
        """在两个建筑之间创建一条路径。"""
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
        
        self._distance_matrix = None # 连接新路径后，距离缓存失效
        return forward

    # --- 以下函数可以被安全删除 ---
    # def find_shortest_path(
    #     self, start_id: str, end_id: str, base_speed: float = 80.0
    # ) -> Optional[List[Building]]:
    #     """
    #     使用Dijkstra算法寻找考虑当前拥塞的【最快】路径。
    #     返回一个建筑列表作为路径，如果找不到路径则返回None。
    #     """
    #     start_node = self._require_building(start_id)
    #     pq = [(0, start_node.building_id, [start_node])]
    #     min_costs = {start_node.building_id: 0}
        
    #     while pq:
    #         cost, current_id, path_list = heapq.heappop(pq)

    #         if cost > min_costs.get(current_id, float('inf')):
    #             continue

    #         if current_id == end_id:
    #             return path_list

    #         current_building = self.buildings[current_id]
    #         for path_edge in current_building.paths:
    #             neighbor_id = path_edge.end.building_id
    #             travel_time = path_edge.get_travel_time(base_speed)
    #             new_cost = cost + travel_time

    #             if new_cost < min_costs.get(neighbor_id, float('inf')):
    #                 min_costs[neighbor_id] = new_cost
    #                 new_path_list = path_list + [path_edge.end]
    #                 heapq.heappush(pq, (new_cost, neighbor_id, new_path_list))

    #     return None
    # --- 删除结束 ---

    def get_path_distance(self, start_id: str, end_id: str) -> Optional[float]:
        """
        使用预计算的距离矩阵快速获取两点间的【最短物理距离】。
        这是奖励塑形（Reward Shaping）的关键。
        """
        if self._distance_matrix is None:
            self._compute_all_pairs_shortest_paths()
        
        return self._distance_matrix.get(start_id, {}).get(end_id)

    def _compute_all_pairs_shortest_paths(self) -> None:
        """
        使用Floyd-Warshall算法计算所有节点对之间的最短物理距离，并缓存结果。
        这个方法只在第一次调用 get_path_distance 时执行一次。
        """
        print("首次计算全图节点距离矩阵 (Floyd-Warshall)...")
        dist: Dict[str, Dict[str, float]] = {b: {b2: float('inf') for b2 in self.buildings} for b in self.buildings}

        for building_id, building in self.buildings.items():
            dist[building_id][building_id] = 0
            for path in building.paths:
                dist[path.start.building_id][path.end.building_id] = path.length

        nodes = list(self.buildings.keys())
        for k in nodes:
            for i in nodes:
                for j in nodes:
                    if dist[i][j] > dist[i][k] + dist[k][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
        
        self._distance_matrix = dist
        print("距离矩阵计算完成。")

    def _require_building(self, building_id: str) -> Building:
        if building_id not in self.buildings:
            raise ValueError(f"Building {building_id} not found")
        return self.buildings[building_id]

    def get_path(self, start_id: str, end_id: str) -> Path:
        """返回两个建筑之间的直接路径对象。"""
        start = self._require_building(start_id)
        for path in start.paths:
            if path.end.building_id == end_id:
                return path
        raise ValueError(f"Path from {start_id} to {end_id} not found")

    def get_building(self, building_id: str) -> Building:
        """返回指定ID的建筑对象。"""
        return self._require_building(building_id)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Graph(buildings={list(self.buildings)})"

__all__ = ["Building", "Path", "Graph"]
