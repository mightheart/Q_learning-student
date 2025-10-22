"""Queue management system for congestion control."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from .graph import Path
    from .student import Student


@dataclass
class QueueStatistics:
    """Statistics for monitoring queue performance."""
    
    total_enqueued: int = 0  # 总入队人数
    total_dequeued: int = 0  # 总出队人数
    max_queue_length: int = 0  # 历史最大队列长度
    total_wait_time: float = 0.0  # 累计等待时间（分钟）
    overflow_count: int = 0  # 队列满溢次数
    
    @property
    def average_wait_time(self) -> float:
        """Calculate average wait time per student."""
        if self.total_dequeued == 0:
            return 0.0
        return self.total_wait_time / self.total_dequeued
    
    @property
    def current_waiting(self) -> int:
        """Calculate number of students currently waiting."""
        return self.total_enqueued - self.total_dequeued


class QueueManager:
    """Manages FIFO queues for bridge paths with capacity limits."""
    
    def __init__(self) -> None:
        """Initialize the queue manager."""
        self._statistics: Dict[str, QueueStatistics] = {}
        self._enqueue_times: Dict[str, Dict[str, float]] = {}  # path_id -> {student_id: enqueue_time}
    
    def _get_path_id(self, path: Path) -> str:
        """Generate unique identifier for a path."""
        return f"{path.start.building_id}->{path.end.building_id}"
    
    def _get_stats(self, path: Path) -> QueueStatistics:
        """Get or create statistics for a path."""
        path_id = self._get_path_id(path)
        if path_id not in self._statistics:
            self._statistics[path_id] = QueueStatistics()
        return self._statistics[path_id]
    
    def can_enqueue(self, path: Path, student: Student) -> bool:
        """Check if a student can join the queue.
        
        Args:
            path: The path to check
            student: The student attempting to join
            
        Returns:
            True if the queue has space, False if full
        """
        # Check if queue is at capacity
        if not path.can_join_queue():
            return False
        
        # Check if student is already in queue (防止重复入队)
        if student in path.queue:
            return False
        
        return True
    
    def enqueue(self, path: Path, student: Student, current_time: float) -> bool:
        """Add a student to the path's queue.
        
        Args:
            path: The path to join
            student: The student joining the queue
            current_time: Current simulation time in minutes
            
        Returns:
            True if successfully enqueued, False if queue is full
        """
        if not self.can_enqueue(path, student):
            # Record overflow
            stats = self._get_stats(path)
            stats.overflow_count += 1
            return False
        
        # Add to queue
        path.queue.append(student)
        student.in_queue = True
        student.queued_path = path
        
        # Record enqueue time
        path_id = self._get_path_id(path)
        if path_id not in self._enqueue_times:
            self._enqueue_times[path_id] = {}
        self._enqueue_times[path_id][student.id] = current_time
        
        # Update statistics
        stats = self._get_stats(path)
        stats.total_enqueued += 1
        stats.max_queue_length = max(stats.max_queue_length, len(path.queue))
        
        return True
    
    def dequeue(self, path: Path, current_time: float) -> Optional[Student]:
        """Remove and return the first student from the queue (FIFO).
        
        Args:
            path: The path to dequeue from
            current_time: Current simulation time in minutes
            
        Returns:
            The dequeued student, or None if queue is empty
        """
        if not path.queue:
            return None
        
        # FIFO: remove first student
        student = path.queue.pop(0)
        student.in_queue = False
        student.queued_path = None
        
        # Calculate wait time
        path_id = self._get_path_id(path)
        if path_id in self._enqueue_times and student.id in self._enqueue_times[path_id]:
            enqueue_time = self._enqueue_times[path_id][student.id]
            wait_time = current_time - enqueue_time
            
            # Update statistics
            stats = self._get_stats(path)
            stats.total_dequeued += 1
            stats.total_wait_time += wait_time
            
            # Clean up enqueue time record
            del self._enqueue_times[path_id][student.id]
        
        return student
    
    def get_queue_position(self, path: Path, student: Student) -> Optional[int]:
        """Get the student's position in the queue (0-indexed).
        
        Args:
            path: The path to check
            student: The student to find
            
        Returns:
            Queue position (0 = first), or None if not in queue
        """
        try:
            return path.queue.index(student)
        except ValueError:
            return None
    
    def get_estimated_wait_time(self, path: Path, student: Student) -> float:
        """Calculate estimated wait time for a student in queue.
        
        Args:
            path: The path the student is queued for
            student: The student to calculate for
            
        Returns:
            Estimated wait time in minutes
        """
        position = self.get_queue_position(path, student)
        if position is None:
            return 0.0
        
        # Estimate based on position and base wait time
        return position * path.base_wait_time_per_student
    
    def clear_queue(self, path: Path) -> List[Student]:
        """Remove all students from a queue (emergency clear).
        
        Args:
            path: The path to clear
            
        Returns:
            List of students that were removed
        """
        removed_students = []
        while path.queue:
            student = path.queue.pop(0)
            student.in_queue = False
            student.queued_path = None
            removed_students.append(student)
        
        return removed_students
    
    def get_statistics(self, path: Optional[Path] = None) -> Dict[str, QueueStatistics]:
        """Get queue statistics.
        
        Args:
            path: Specific path to get stats for, or None for all paths
            
        Returns:
            Dictionary mapping path_id to statistics
        """
        if path is not None:
            path_id = self._get_path_id(path)
            return {path_id: self._get_stats(path)}
        
        return self._statistics.copy()
    
    def reset_statistics(self) -> None:
        """Reset all statistics (for testing or new simulation runs)."""
        self._statistics.clear()
        self._enqueue_times.clear()


__all__ = ["QueueManager", "QueueStatistics"]
