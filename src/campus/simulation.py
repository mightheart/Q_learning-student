"""Simulation engine coordinating students and time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .graph import Graph
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

    def __init__(self, graph: Graph, clock: Optional[SimulationClock] = None) -> None:
        self.graph = graph
        self.clock = clock or SimulationClock()
        self.students: List[Student] = []
        self.event_log: List[SimulationEvent] = []

    def add_students(self, students: Iterable[Student]) -> None:
        """Add a collection of students into the simulation."""

        self.students.extend(students)

    def step(self, delta_seconds: float) -> None:
        """Advance the simulation by ``delta_seconds`` of real time."""

        delta_minutes = self.clock.tick(delta_seconds)
        current_time = self.clock.current_time_str

        for student in self.students:
            previous_state = student.state
            if student.state != "moving":
                student.plan_next_move(current_time, self.graph)
            student.update(delta_minutes)
            if previous_state != "in_class" and student.state == "in_class" and student.active_event:
                self._log_event(student, f"Arrived at {student.current_location.name}")

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
