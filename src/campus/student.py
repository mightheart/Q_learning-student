"""Student agent implementation for the campus simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .graph import Building, Graph, Path
from .queue_manager import QueueManager
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
        queue_manager: Optional[QueueManager] = None,
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
        
        # Phase 1: Deadline and ETA tracking
        self.deadline: Optional[float] = None  # 当前目标的截止时间（分钟）
        self.eta: Optional[float] = None  # 预计到达时间（分钟）
        self.buffer_time: float = 5.0  # 时间缓冲（分钟）
        self.last_replan_time: Optional[float] = None  # 上次重新规划的时间
        self.in_queue: bool = False  # 是否在队列中等待
        self.queued_path: Optional[Path] = None  # 正在排队的路径
        
        # Phase 3.2: Queue manager reference
        self._queue_manager: Optional[QueueManager] = queue_manager
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
            self.deadline = None  # Phase 5: Clear deadline
            return None

        target = graph.get_building(next_event.building_id)
        if self.current_location.building_id == target.building_id:
            self.state = "in_class"
            self._clear_plan()
            self._active_event = next_event
            self.deadline = None  # Phase 5: Already at destination
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
        
        # Phase 5: Set deadline for this movement
        # Deadline = event time - buffer time
        self.deadline = float(next_event.minutes) - self.buffer_time
        
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
            
            # 🌉 Phase 3.2: Bridge queue management
            if not segment.started and segment.path.is_bridge and segment.path.capacity is not None:
                # Use queue system if queue_manager is available
                if self._queue_manager is not None and not self.in_queue:
                    # Check if we need to join queue
                    if not segment.path.has_capacity():
                        # Path is full, try to join queue
                        # Note: We'll use a dummy current_time here, real time comes from simulation
                        # This is a limitation - ideally we'd pass current_time to update()
                        if self._queue_manager.can_enqueue(segment.path, self):
                            # Join queue and wait
                            # Actual enqueue will be handled by simulation
                            self.state = "waiting"
                            self._wait_time = 0.0
                            return
                        else:
                            # Queue is full, try to reroute
                            self.state = "waiting"
                            self._wait_time = 0.0
                            return
                    # Path has capacity, proceed
                else:
                    # Fallback to old congestion check (for backward compatibility)
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
        """Calculate the total cost (travel time + queue wait) of the current path.
        
        Phase 2: Now uses get_total_crossing_cost() to include queue wait times.
        """
        
        if not self._segments:
            return 0.0
        
        total_cost = 0.0
        for segment in self._segments:
            total_cost += segment.path.get_total_crossing_cost()
        
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
    
    def calculate_eta(self, current_time: float) -> Optional[float]:
        """Calculate estimated time of arrival (ETA) at the current destination.
        
        Phase 5.1: Calculates ETA by summing remaining time in current segment
        plus total crossing cost of all future segments.
        
        Args:
            current_time: Current simulation time in minutes
            
        Returns:
            Estimated arrival time in minutes, or None if not moving
        """
        if not self._segments or self.state != "moving":
            return None
        
        # Start with current time
        eta = current_time
        
        # Add remaining time in current segment
        if self._segments:
            eta += self._segments[0].remaining_time
        
        # Add cost of all future segments
        for segment in self._segments[1:]:
            eta += segment.path.get_total_crossing_cost()
        
        # Update the eta attribute
        self.eta = eta
        return eta
    
    def is_deadline_at_risk(self, current_time: float, threshold: float = 0.8) -> bool:
        """Check if the student is at risk of missing their deadline.
        
        Phase 5.2: Compares ETA with deadline to determine if replanning is needed.
        
        Args:
            current_time: Current simulation time in minutes
            threshold: Risk threshold (0.0-1.0). 1.0 means only replan when ETA > deadline.
                      0.8 means replan when buffer is reduced to 20% or less.
            
        Returns:
            True if deadline is at risk, False otherwise
        """
        if self.deadline is None or not self._segments:
            return False
        
        # Calculate current ETA
        eta = self.calculate_eta(current_time)
        if eta is None:
            return False
        
        # Calculate time buffer remaining
        time_to_deadline = self.deadline - current_time
        time_needed = eta - current_time
        
        # Risk if: time_needed > time_to_deadline * threshold
        # Example: threshold=0.8 means if we need 9 min but only have 10 min buffer,
        # we're at risk (9 > 10*0.8 = 8)
        return time_needed > time_to_deadline * threshold
    
    def replan_if_needed(self, current_time: float, graph: Graph, cooldown: float = 2.0) -> bool:
        """Attempt to replan route if deadline is at risk.
        
        Phase 5.3: Proactive replanning to avoid missing deadlines.
        Includes cooldown to prevent excessive replanning.
        
        Args:
            current_time: Current simulation time in minutes
            graph: Graph for pathfinding
            cooldown: Minimum time (minutes) between replans
            
        Returns:
            True if replanning was performed, False otherwise
        """
        # Check cooldown
        if self.last_replan_time is not None:
            time_since_replan = current_time - self.last_replan_time
            if time_since_replan < cooldown:
                return False  # Too soon to replan
        
        # Check if deadline is at risk
        if not self.is_deadline_at_risk(current_time):
            return False  # No need to replan
        
        # Need to replan - find alternative route
        if not self._last_graph or not self._active_event:
            return False  # No graph or destination
        
        target_id = self._active_event.building_id
        start_id = self.current_location.building_id
        
        if start_id == target_id:
            return False  # Already at destination
        
        try:
            # Try to find an alternative (second shortest) path
            second_cost = graph.find_second_shortest_path(start_id, target_id)
            
            # Check if alternative path would help
            # (It might be worse due to current congestion)
            current_cost = self.get_current_path_cost()
            
            # Only replan if alternative is actually better
            # (considering current queue states)
            if second_cost < current_cost:
                # Clear current plan
                self._clear_plan()
                
                # Find and set new route
                # Note: find_shortest_path now returns the best path considering queues
                # So we need to temporarily block current path to force alternative
                # For simplicity, we'll just replan and trust the congestion-aware algorithm
                total_time, route = graph.find_shortest_path(start_id, target_id)
                
                # Create new segments
                segments: List[_Segment] = []
                for start, end in zip(route, route[1:]):
                    path = graph.get_path(start.building_id, end.building_id)
                    segments.append(_Segment(path=path, remaining_time=path.get_travel_time()))
                
                self.state = "moving"
                self.path_to_destination = route
                self._segments = segments
                self._current_segment_index = 0
                self.last_replan_time = current_time
                
                return True
        except ValueError:
            # No alternative path available
            return False
        
        return False
    
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
