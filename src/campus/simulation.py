"""Simulation engine coordinating students and time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .graph import Graph
from .queue_manager import QueueManager
from .release_controller import ReleaseController, ReleaseConfig
from .student import Student


MINUTES_PER_DAY = 24 * 60


def _parse_time(time_str: str) -> int:
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be in HH:MM format")
    hour, minute = (int(value) for value in parts)
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("Time components out of range")
    return hour * 60 + minute


def _format_time(total_minutes: float) -> str:
    minutes = int(total_minutes) % MINUTES_PER_DAY
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


class SimulationClock:
    """Keeps track of simulated time progression."""

    def __init__(self, start_time: str = "07:00", time_scale: float = 1.0) -> None:
        if time_scale <= 0:
            raise ValueError("time_scale must be positive")
        self.time_scale = time_scale
        self._current_minutes: float = float(_parse_time(start_time))

    def tick(self, delta_seconds: float) -> float:
        """Advance the clock and return simulated minutes progressed."""

        if delta_seconds < 0:
            raise ValueError("delta_seconds must be non-negative")
        simulated_seconds = delta_seconds * self.time_scale
        simulated_minutes = simulated_seconds / 60.0
        self._current_minutes = (self._current_minutes + simulated_minutes) % MINUTES_PER_DAY
        return simulated_minutes

    @property
    def current_time_str(self) -> str:
        """Return the current simulated time as ``HH:MM``."""

        return _format_time(self._current_minutes)

    @property
    def current_minutes(self) -> float:
        """Return the current simulated minutes since midnight."""

        return self._current_minutes


@dataclass
class SimulationEvent:
    """Represents a notable occurrence in the simulation."""

    timestamp: str
    student_id: str
    description: str


class Simulation:
    """Main simulation loop driving student updates."""

    def __init__(
        self, 
        graph: Graph, 
        clock: Optional[SimulationClock] = None,
        release_config: Optional[ReleaseConfig] = None,
    ) -> None:
        self.graph = graph
        self.clock = clock or SimulationClock()
        self.students: List[Student] = []
        self.event_log: List[SimulationEvent] = []
        # Phase 3: Queue management system
        self.queue_manager = QueueManager()
        # Phase 4: Batch release controller
        self.release_controller = ReleaseController(release_config)

    def add_students(self, students: Iterable[Student]) -> None:
        """Add a collection of students into the simulation."""

        for student in students:
            # Phase 3.2: Inject queue_manager into each student
            student._queue_manager = self.queue_manager
            self.students.append(student)

    def step(self, delta_seconds: float) -> None:
        """Advance the simulation by ``delta_seconds`` of real time."""

        delta_minutes = self.clock.tick(delta_seconds)
        current_time = self.clock.current_time_str

        # Phase 3.3: Process queues - release students when capacity available
        self._process_queues()
        
        # Phase 4.2: Update release controller and get students ready to depart
        released_students = self.release_controller.update(delta_minutes)
        
        # Track students who finish class in this frame (for batch release)
        students_finished_class = []

        for student in self.students:
            previous_state = student.state
            
            # Phase 5: Proactive replanning for students at risk of missing deadline
            if student.state == "moving" and student._segments:
                student.replan_if_needed(self.clock.current_minutes, self.graph)
            
            # Phase 3.2: Check if student needs to join a queue
            if student.state == "waiting" and not student.in_queue and student._segments:
                # Student is waiting and not yet in queue
                next_segment = student._segments[0]
                if next_segment.path.is_bridge and not next_segment.started:
                    # Try to enqueue
                    if self.queue_manager.can_enqueue(next_segment.path, student):
                        self.queue_manager.enqueue(next_segment.path, student, self.clock.current_minutes)
            
            # Phase 4.2: Check if student should be allowed to plan next move
            # Allow planning if:
            # 1. Student is not moving AND not in class, OR
            # 2. Student is in class but was just released from batch controller
            should_plan = student.state != "moving"
            
            # Special case: if student is idle after class, don't plan yet
            # (they should be in release_controller or already released)
            if student.state == "idle" and student not in released_students:
                # Check if they're waiting to be released
                if student in self.release_controller._pending_students:
                    should_plan = False  # Wait for batch release
                else:
                    should_plan = True  # Not in release queue, can plan normally
            
            if should_plan:
                student.plan_next_move(current_time, self.graph)
            
            student.update(delta_minutes)
            
            # Phase 4.2: Detect students who just finished class
            if previous_state == "in_class" and student.state != "in_class":
                students_finished_class.append(student)
            
            if previous_state != "in_class" and student.state == "in_class" and student.active_event:
                self._log_event(student, f"Arrived at {student.current_location.name}")
        
        # Phase 4.2: Add students who finished class to release controller
        if students_finished_class:
            self.release_controller.add_students(students_finished_class)
    
    def _process_queues(self) -> None:
        """Process all queues and release students when capacity is available.
        
        Phase 3.3: Check each path's queue and release waiting students
        when the path has available capacity.
        """
        # Collect all paths with queues (using list to avoid hashability issues)
        paths_with_queues = []
        for student in self.students:
            if student.queued_path is not None and student.queued_path not in paths_with_queues:
                paths_with_queues.append(student.queued_path)
        
        # Process each queue
        for path in paths_with_queues:
            # Release students while path has capacity and queue is not empty
            while path.queue and path.has_capacity():
                student = self.queue_manager.dequeue(path, self.clock.current_minutes)
                if student:
                    # Student can now start moving on this path
                    # The actual movement will be handled in student.update()
                    pass
                    # Student can now start moving on this path
                    # The actual movement will be handled in student.update()
                    pass

    def _log_event(self, student: Student, message: str) -> None:
        """Append a formatted event to the event log."""

        self.event_log.append(
            SimulationEvent(
                timestamp=self.clock.current_time_str,
                student_id=student.id,
                description=message,
            )
        )


__all__ = ["SimulationClock", "Simulation", "SimulationEvent"]
