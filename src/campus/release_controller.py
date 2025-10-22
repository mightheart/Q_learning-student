"""Batch release controller for temporal traffic distribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .student import Student


@dataclass
class ReleaseConfig:
    """Configuration for batch release behavior."""
    
    batch_size: int = 10  # 每批次释放的学生数量
    release_interval: float = 0.5  # 批次之间的间隔（分钟）
    enabled: bool = True  # 是否启用批次释放
    
    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.release_interval < 0:
            raise ValueError("release_interval must be non-negative")


class ReleaseController:
    """Controls batch release of students to distribute traffic over time.
    
    Phase 4: 时间分流策略
    - 避免所有学生同时出发造成拥塞
    - 按批次（batch）释放学生
    - 批次之间有时间间隔，平滑流量
    """
    
    def __init__(self, config: Optional[ReleaseConfig] = None) -> None:
        """Initialize the release controller.
        
        Args:
            config: Release configuration. If None, uses default settings.
        """
        self.config = config or ReleaseConfig()
        self._pending_students: List[Student] = []  # 待释放学生队列
        self._time_since_last_release: float = 0.0  # 距离上次释放的时间
        self._total_released: int = 0  # 总共释放的学生数
        self._total_batches: int = 0  # 总批次数
    
    def add_students(self, students: List[Student]) -> None:
        """Add students to the pending release queue.
        
        Phase 4: 当下课时，将所有学生添加到待释放队列
        而不是立即让他们全部出发。
        
        Args:
            students: List of students to be released in batches
        """
        self._pending_students.extend(students)
    
    def update(self, delta_time: float) -> List[Student]:
        """Update release timer and return students ready to depart.
        
        Phase 4: 每帧调用，检查是否该释放下一批学生。
        
        Args:
            delta_time: Time elapsed since last update (minutes)
            
        Returns:
            List of students released in this update (may be empty)
        """
        if not self.config.enabled:
            # Batch release disabled, release all immediately
            released = self._pending_students.copy()
            self._pending_students.clear()
            self._total_released += len(released)
            return released
        
        if not self._pending_students:
            # No students pending
            return []
        
        self._time_since_last_release += delta_time
        
        # Check if it's time to release next batch
        if self._time_since_last_release >= self.config.release_interval:
            # Release next batch
            batch_size = min(self.config.batch_size, len(self._pending_students))
            released = self._pending_students[:batch_size]
            self._pending_students = self._pending_students[batch_size:]
            
            # Update statistics
            self._total_released += batch_size
            self._total_batches += 1
            self._time_since_last_release = 0.0  # Reset timer
            
            return released
        
        # Not time yet, no release
        return []
    
    def get_pending_count(self) -> int:
        """Get number of students waiting to be released."""
        return len(self._pending_students)
    
    def get_estimated_wait_time(self) -> float:
        """Estimate how long until all pending students are released.
        
        Returns:
            Estimated time in minutes
        """
        if not self._pending_students:
            return 0.0
        
        if not self.config.enabled:
            return 0.0
        
        # Calculate remaining batches
        remaining_batches = (len(self._pending_students) + self.config.batch_size - 1) // self.config.batch_size
        
        # Time for remaining batches
        time_for_batches = remaining_batches * self.config.release_interval
        
        # Subtract time already elapsed in current interval
        return time_for_batches - self._time_since_last_release
    
    def clear(self) -> List[Student]:
        """Clear pending queue and return all students (emergency release).
        
        Returns:
            All pending students
        """
        released = self._pending_students.copy()
        self._pending_students.clear()
        self._total_released += len(released)
        return released
    
    def reset(self) -> None:
        """Reset controller state (for new simulation runs)."""
        self._pending_students.clear()
        self._time_since_last_release = 0.0
        self._total_released = 0
        self._total_batches = 0
    
    def get_statistics(self) -> dict:
        """Get release statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_released": self._total_released,
            "total_batches": self._total_batches,
            "pending_count": len(self._pending_students),
            "avg_batch_size": self._total_released / self._total_batches if self._total_batches > 0 else 0.0,
            "estimated_wait_time": self.get_estimated_wait_time(),
        }


__all__ = ["ReleaseController", "ReleaseConfig"]
