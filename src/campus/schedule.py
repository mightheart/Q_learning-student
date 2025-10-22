"""Schedule management for classes within the simulation."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from typing import List, Optional, Tuple


def _time_to_minutes(time_str: str) -> int:
    """Convert ``HH:MM`` formatted string into total minutes."""

    hour, minute = time_str.split(":")
    total = int(hour) * 60 + int(minute)
    if total < 0 or total >= 24 * 60:
        raise ValueError("Time must be within a single day")
    return total


@dataclass(frozen=True)
class ScheduleEvent:
    """将时间与目的地建筑关联的单个日程条目。"""

    time_str: str
    building_id: str
    duration: int  # 新增：事件的持续时间（分钟）

    @property
    def start_minutes(self) -> int:
        """事件开始时间（分钟）。"""
        return _time_to_minutes(self.time_str)

    @property
    def end_minutes(self) -> int:
        """事件结束时间（分钟）。"""
        return self.start_minutes + self.duration


class Schedule:
    """Simple in-memory schedule for a class."""

    def __init__(self, class_name: str) -> None:
        self.class_name = class_name
        self._events: List[ScheduleEvent] = []
        self._event_minutes: List[int] = []
        
        # Phase 1: Travel buffer configuration
        self.travel_buffer: float = 5.0  # 出发前的时间缓冲（分钟）

    def add_event(self, time_str: str, building_id: str, duration: int) -> None:
        """插入一个新事件，同时保持内部顺序排序。"""

        minutes = _time_to_minutes(time_str)
        # 修改：创建事件时传入 duration
        event = ScheduleEvent(time_str=time_str, building_id=building_id, duration=duration)
        position = bisect_right(self._event_minutes, minutes)
        self._event_minutes.insert(position, minutes)
        self._events.insert(position, event)

    def get_current_event(self, current_time: str) -> Optional[ScheduleEvent]:
        """新增：获取当前时间正在进行的事件。"""
        current_minutes = _time_to_minutes(current_time)
        # 寻找最后一个开始时间 <= 当前时间的事件
        index = bisect_right(self._event_minutes, current_minutes) - 1
        
        if index < 0:
            return None
            
        event = self._events[index]
        # 检查当前时间是否在该事件的时间范围内
        if event.start_minutes <= current_minutes < event.end_minutes:
            return event
            
        return None

    def get_next_event(self, current_time: str) -> Optional[ScheduleEvent]:
        """Return the first event strictly after ``current_time``."""

        current_minutes = _time_to_minutes(current_time)
        index = bisect_right(self._event_minutes, current_minutes)
        if index >= len(self._events):
            return None
        return self._events[index]

    def upcoming_events(self, current_time: str) -> List[ScheduleEvent]:
        """Return all events after the provided time."""

        current_minutes = _time_to_minutes(current_time)
        index = bisect_right(self._event_minutes, current_minutes)
        return self._events[index:]
    
    def get_next_deadline(self, current_minutes: float) -> Optional[float]:
        """Return the deadline (in minutes) for the next scheduled event.
        
        The deadline is calculated as: event_time - travel_buffer
        This gives students time to plan their route and travel.
        
        Args:
            current_minutes: Current simulation time in minutes
            
        Returns:
            Deadline time in minutes, or None if no upcoming events
        """
        index = bisect_right(self._event_minutes, int(current_minutes))
        if index >= len(self._events):
            return None
        
        next_event_time = self._event_minutes[index]
        return float(next_event_time) - self.travel_buffer

    def __iter__(self):  # pragma: no cover - helper for debugging
        return iter(self._events)

    def __len__(self) -> int:  # pragma: no cover - helper for debugging
        return len(self._events)


__all__ = ["Schedule", "ScheduleEvent"]
