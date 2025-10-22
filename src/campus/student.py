"""Student agent implementation for the campus simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .graph import Building, Graph, Path
from .schedule import Schedule, ScheduleEvent


@dataclass
class _Segment:
    """Represents progress travelling along a path."""

    path: Path
    remaining_time: float
    started: bool = False

    def step(self, student_id: str, delta_time: float) -> float:
        """Advance along the path and return leftover time."""

        if not self.started:
            if not self.path.has_capacity():
                raise RuntimeError("Path capacity exceeded")
            self.path.current_students.append(student_id)
            self.started = True

        if delta_time < self.remaining_time:
            self.remaining_time -= delta_time
            return 0.0

        delta_time -= self.remaining_time
        self.remaining_time = 0.0
        if student_id in self.path.current_students:
            self.path.current_students.remove(student_id)
        return delta_time


class Student:
    """Represents a moving student agent with a schedule."""

    def __init__(
        self,
        student_id: str,
        class_name: str,
        schedule: Schedule,
        start_building: Building,
    ) -> None:
        self.id = student_id
        self.class_name = class_name
        self.schedule = schedule
        self.current_location: Building = start_building
        self.state: str = "idle"  # idle, moving, waiting, in_class
        self.path_to_destination: List[Building] = []
        self._segments: List[_Segment] = []
        self._active_event: Optional[ScheduleEvent] = None
        
        # Animation state for smooth movement
        self._animation_progress: float = 0.0  # 0.0 to 1.0 along current segment
        self._current_segment_index: int = 0
        
        # Bridge congestion management
        self._wait_time: float = 0.0  # How long student has been waiting
        self._max_wait_time: float = 2.0  # Maximum wait time (minutes) before rerouting
        self._congestion_threshold: float = 0.7  # Don't enter bridge if >70% full
        self._last_graph: Optional[Graph] = None  # Keep reference for rerouting

    def plan_next_move(self, current_time: str, graph: Graph) -> Optional[ScheduleEvent]:
        """Plan a route towards the next scheduled event."""

        self._last_graph = graph  # Store for potential rerouting
        
        next_event = self.schedule.get_next_event(current_time)
        if next_event is None:
            self._clear_plan()
            return None

        target = graph.get_building(next_event.building_id)
        if self.current_location.building_id == target.building_id:
            self.state = "in_class"
            self._clear_plan()
            self._active_event = next_event
            return next_event

        # Clear old path data completely before planning new route
        self._clear_plan()
        
        total_time, route = graph.find_shortest_path(
            self.current_location.building_id, target.building_id
        )
        if len(route) < 2:
            raise RuntimeError("Route must contain at least two buildings")

        segments: List[_Segment] = []
        for start, end in zip(route, route[1:]):
            path = graph.get_path(start.building_id, end.building_id)
            segments.append(_Segment(path=path, remaining_time=path.get_travel_time()))

        self.state = "moving"
        self.path_to_destination = route
        self._segments = segments
        self._active_event = next_event
        self._current_segment_index = 0
        self._wait_time = 0.0  # Reset wait time
        return next_event

    def update(self, delta_time: float) -> None:
        """Advance the student's movement state."""

        # Handle waiting state
        if self.state == "waiting":
            self._wait_time += delta_time
            
            # Check if wait time exceeded
            if self._wait_time >= self._max_wait_time:
                # Give up waiting, try to reroute
                if self._last_graph and self._active_event:
                    target = self._last_graph.get_building(self._active_event.building_id)
                    try:
                        # Clean up old path data first
                        self._clear_plan()
                        
                        # Attempt to find alternative route
                        total_time, route = self._last_graph.find_shortest_path(
                            self.current_location.building_id, target.building_id
                        )
                        # Create new segments
                        segments: List[_Segment] = []
                        for start, end in zip(route, route[1:]):
                            path = self._last_graph.get_path(start.building_id, end.building_id)
                            segments.append(_Segment(path=path, remaining_time=path.get_travel_time()))
                        
                        self.state = "moving"
                        self.path_to_destination = route
                        self._segments = segments
                        self._active_event = self._active_event  # Restore active event
                        self._wait_time = 0.0
                        self._current_segment_index = 0
                    except ValueError:
                        # No alternative route, continue waiting
                        self._wait_time = 0.0  # Reset to wait again
                return
            
            # Check if next segment (bridge) has capacity now
            if self._segments:
                next_segment = self._segments[0]
                if next_segment.path.is_bridge and next_segment.path.capacity is not None:
                    occupancy_ratio = len(next_segment.path.current_students) / next_segment.path.capacity
                    # If congestion cleared enough, resume moving
                    if occupancy_ratio < self._congestion_threshold:
                        self.state = "moving"
                        self._wait_time = 0.0
            return

        if self.state != "moving" or not self._segments:
            return

        remaining = delta_time
        while remaining > 0.0 and self._segments:
            segment = self._segments[0]
            self._current_segment_index = 0
            
            # 🌉 Bridge congestion check: Before entering a bridge
            if not segment.started and segment.path.is_bridge and segment.path.capacity is not None:
                # Check current congestion level
                occupancy_ratio = len(segment.path.current_students) / segment.path.capacity
                
                if occupancy_ratio >= self._congestion_threshold:
                    # Bridge is too congested, switch to waiting state
                    self.state = "waiting"
                    self._wait_time = 0.0
                    return
            
            before = remaining
            remaining = segment.step(self.id, remaining)
            if segment.remaining_time == 0.0:
                self.current_location = segment.path.end
                self._segments.pop(0)
                self._current_segment_index = 0
            if remaining == before:
                break

        if not self._segments:
            self.state = "in_class" if self._active_event else "idle"
            self.path_to_destination = [self.current_location]

    def _clear_plan(self) -> None:
        """Reset the current movement plan."""

        for segment in self._segments:
            if segment.started and self.id in segment.path.current_students:
                segment.path.current_students.remove(self.id)
        self._segments = []
        self.path_to_destination = [self.current_location]
        self._active_event = None
        if self.state == "moving":
            self.state = "idle"

    @property
    def active_event(self) -> Optional[ScheduleEvent]:
        """Return the event the student is currently targeting."""

        return self._active_event
    
    def get_current_path_cost(self) -> float:
        """Calculate the total cost (travel time) of the current path."""
        
        if not self._segments:
            return 0.0
        
        total_cost = 0.0
        for segment in self._segments:
            total_cost += segment.path.get_travel_time()
        
        return total_cost
    
    def get_alternative_path_cost(self) -> Optional[float]:
        """Calculate the cost of the second-best alternative path to the current destination.
        
        Returns None if no alternative path exists or if not currently moving.
        """
        
        if not self._last_graph or not self._active_event or not self.path_to_destination:
            return None
        
        target_id = self._active_event.building_id
        start_id = self.current_location.building_id
        
        if start_id == target_id:
            return None
        
        try:
            # Get current path for reference
            current_cost, _ = self._last_graph.find_shortest_path(start_id, target_id)
            
            # Try to find second shortest path
            second_cost = self._last_graph.find_second_shortest_path(start_id, target_id)
            
            return second_cost
        except (ValueError, AttributeError):
            return None
    
    def get_interpolated_position(self) -> Tuple[float, float]:
        """Get the smooth interpolated position for animation using Manhattan-style paths."""
        
        if self.state != "moving" or not self._segments:
            return (float(self.current_location.x), float(self.current_location.y))
        
        # Get current segment
        if self._current_segment_index >= len(self._segments):
            return (float(self.current_location.x), float(self.current_location.y))
        
        segment = self._segments[self._current_segment_index]
        
        # Calculate progress (0.0 = start, 1.0 = end)
        if segment.path.get_travel_time() > 0:
            progress = 1.0 - (segment.remaining_time / segment.path.get_travel_time())
        else:
            progress = 1.0
        
        progress = max(0.0, min(1.0, progress))
        
        # Get start and end positions
        start_x = float(segment.path.start.x)
        start_y = float(segment.path.start.y)
        end_x = float(segment.path.end.x)
        end_y = float(segment.path.end.y)
        
        # Manhattan-style movement: move horizontally first, then vertically
        # This ensures students follow the grid-based road network
        
        if start_x == end_x or start_y == end_y:
            # Straight path (already aligned) - simple linear interpolation
            current_x = start_x + (end_x - start_x) * progress
            current_y = start_y + (end_y - start_y) * progress
        else:
            # L-shaped path: horizontal then vertical
            # Calculate total Manhattan distance
            dx = abs(end_x - start_x)
            dy = abs(end_y - start_y)
            total_distance = dx + dy
            
            if total_distance > 0:
                # Determine which portion of journey we're in
                horizontal_distance = dx
                traveled_distance = total_distance * progress
                
                if traveled_distance <= horizontal_distance:
                    # Still moving horizontally
                    horizontal_progress = traveled_distance / horizontal_distance if horizontal_distance > 0 else 1.0
                    current_x = start_x + (end_x - start_x) * horizontal_progress
                    current_y = start_y
                else:
                    # Moving vertically
                    vertical_traveled = traveled_distance - horizontal_distance
                    vertical_progress = vertical_traveled / dy if dy > 0 else 1.0
                    current_x = end_x
                    current_y = start_y + (end_y - start_y) * vertical_progress
            else:
                current_x = end_x
                current_y = end_y
        
        return (current_x, current_y)


__all__ = ["Student"]
