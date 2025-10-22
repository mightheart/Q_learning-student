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
        self.state: str = "idle"
        self.path_to_destination: List[Building] = []
        self._segments: List[_Segment] = []
        self._active_event: Optional[ScheduleEvent] = None
        
        # Animation state for smooth movement
        self._animation_progress: float = 0.0  # 0.0 to 1.0 along current segment
        self._current_segment_index: int = 0

    def plan_next_move(self, current_time: str, graph: Graph) -> Optional[ScheduleEvent]:
        """Plan a route towards the next scheduled event."""

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
        return next_event

    def update(self, delta_time: float) -> None:
        """Advance the student's movement state."""

        if self.state != "moving" or not self._segments:
            return

        remaining = delta_time
        while remaining > 0.0 and self._segments:
            segment = self._segments[0]
            self._current_segment_index = 0
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
    
    def get_interpolated_position(self) -> Tuple[float, float]:
        """Get the smooth interpolated position for animation."""
        
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
        
        # Linear interpolation between start and end
        start_x = float(segment.path.start.x)
        start_y = float(segment.path.start.y)
        end_x = float(segment.path.end.x)
        end_y = float(segment.path.end.y)
        
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress
        
        return (current_x, current_y)


__all__ = ["Student"]
