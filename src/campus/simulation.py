"""模拟引擎，作为Q-learning智能体的“环境”。(最终修复版)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .graph import Graph
from .student import Student


MINUTES_PER_DAY = 24 * 60


def _parse_time(time_str: str) -> int:
    """将 HH:MM 格式的时间字符串解析为从午夜开始的分钟数。"""

    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be in HH:MM format")
    hour, minute = (int(value) for value in parts)
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("Time components out of range")
    return hour * 60 + minute


def _format_time(total_minutes: float) -> str:
    """将总分钟数格式化为 HH:MM 字符串。"""

    minutes = int(total_minutes) % MINUTES_PER_DAY
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


class SimulationClock:
    """跟踪模拟时间的进展。"""

    def __init__(self, start_time: str = "07:00", time_scale: float = 1.0) -> None:
        if time_scale <= 0:
            raise ValueError("time_scale must be positive")
        self.time_scale = time_scale
        # 修改：使用 total_minutes 来避免24小时取余问题
        self._total_minutes: float = float(_parse_time(start_time))

    def tick(self, delta_seconds: float) -> float:
        """推进时钟并返回模拟进行的分钟数。"""

        if delta_seconds < 0:
            raise ValueError("delta_seconds must be non-negative")
        simulated_seconds = delta_seconds * self.time_scale
        simulated_minutes = simulated_seconds / 60.0
        self._total_minutes += simulated_minutes
        return simulated_minutes

    @property
    def current_time_str(self) -> str:
        """将当前模拟时间返回为 HH:MM 格式。"""

        return _format_time(self._total_minutes)

    @property
    def current_minutes(self) -> float:
        """返回自午夜以来的当前模拟分钟数（用于日程表查询）。"""

        return self._total_minutes % MINUTES_PER_DAY


@dataclass
class SimulationEvent:
    """代表模拟中的一个值得注意的事件。"""

    timestamp: str
    student_id: str
    description: str


class Simulation:
    """主模拟循环，驱动学生智能体的更新和学习。"""

    def __init__(
        self, 
        graph: Graph, 
        clock: Optional[SimulationClock] = None,
    ) -> None:
        self.graph = graph
        self.clock = clock or SimulationClock()
        self.students: List[Student] = []
        self.event_log: List[SimulationEvent] = []

    def add_students(self, students: Iterable[Student]) -> None:
        """将学生群体添加到模拟中。"""
        self.students.extend(students)

    def step(self, delta_seconds: float) -> float:
        """将模拟推进一个时间步，并返回推进的分钟数。"""

        delta_minutes = self.clock.tick(delta_seconds)
        current_minutes = self.clock.current_minutes

        for student in self.students:
            # 1. 推进物理状态（移动）
            student.update(delta_minutes, current_minutes)

            # 2. 如果学生处于空闲状态，则进行学习和决策
            if student.state == "idle":
                # 2a. 如果有待学习的动作（刚完成移动或决定等待），则学习
                if student.last_state_action:
                    student.learn(self.graph, current_minutes)
                
                # 2b. 为下一步做决策
                student.decide_and_act(self.graph, current_minutes)
        
        return delta_minutes

    def _log_event(self, student: Student, message: str) -> None:
        """将格式化的事件附加到事件日志中。"""

        self.event_log.append(
            SimulationEvent(
                timestamp=self.clock.current_time_str,
                student_id=student.id,
                description=message,
            )
        )


__all__ = ["SimulationClock", "Simulation", "SimulationEvent"]