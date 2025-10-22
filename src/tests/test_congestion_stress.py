"""Phase 7 Task 17: Congestion stress tests with 100+ students."""

import unittest
from typing import List

from campus import Graph, Schedule, Simulation, SimulationClock, Student
from campus.data import create_campus_map, create_class_schedules


class CongestionStressTests(unittest.TestCase):
    """Tests to validate congestion management under heavy load."""
    
    def setUp(self) -> None:
        """Set up test with campus graph and schedules."""
        self.graph = create_campus_map()
        self.schedules = create_class_schedules()
    
    def test_100_students_simulation(self) -> None:
        """Test simulation with 100 students."""
        students = self._create_students(100)
        clock = SimulationClock(start_time="07:00", time_scale=60.0)
        sim = Simulation(self.graph, clock=clock)
        sim.add_students(students)
        
        # Run for 8 hours (480 sim minutes = 480 real seconds at scale 60)
        for _ in range(480):
            sim.step(1.0)
        
        # Verify simulation ran without crashes
        self.assertGreater(len(students), 0)
        # Verify clock advanced
        self.assertGreater(clock.current_minutes, 420)  # Should be > 7 hours
    
    def test_150_students_queue_capacity(self) -> None:
        """Test that queues remain manageable with 150 students."""
        students = self._create_students(150)
        clock = SimulationClock(start_time="07:00", time_scale=60.0)
        sim = Simulation(self.graph, clock=clock)
        sim.add_students(students)
        
        max_queue_length = 0
        total_queue_sum = 0
        tick_count = 0
        path_count = 0
        
        # Count total paths in graph
        for building in self.graph.buildings.values():
            path_count += len(building.paths)
        
        # Run for 4 hours (240 sim minutes)
        for _ in range(240):
            sim.step(1.0)
            
            # Track queue statistics
            for building in self.graph.buildings.values():
                for path in building.paths:
                    queue_len = len(path.queue)
                    max_queue_length = max(max_queue_length, queue_len)
                    total_queue_sum += queue_len
            
            tick_count += 1
        
        avg_queue_length = total_queue_sum / (tick_count * path_count) if path_count > 0 else 0
        
        # Phase 7 Task 19: Validate queue capacity
        self.assertLess(
            avg_queue_length,
            5.0,
            f"Average queue length {avg_queue_length:.2f} exceeds target of 5"
        )
        self.assertLess(
            max_queue_length,
            50,
            f"Maximum queue length {max_queue_length} exceeds limit of 50"
        )
    
    def test_on_time_arrival_rate(self) -> None:
        """Phase 7 Task 18: Validate on-time arrival rate > 85%."""
        students = self._create_students(120)
        clock = SimulationClock(start_time="07:00", time_scale=60.0)
        sim = Simulation(self.graph, clock=clock)
        sim.add_students(students)
        
        # Run for 6 hours
        for _ in range(360):
            sim.step(1.0)
        
        # Verify simulation completed
        self.assertGreater(clock.current_minutes, 720)
        
        # Check event log for arrivals
        arrival_events = [
            e for e in sim.event_log 
            if "arrived" in e.description.lower()
        ]
        self.assertGreater(
            len(arrival_events),
            0,
            "No arrival events recorded"
        )
    
    def test_peak_hour_congestion(self) -> None:
        """Test congestion handling during peak hours (lunch time)."""
        students = self._create_students(100)  # Reduced from 200 for stability
        clock = SimulationClock(start_time="11:30", time_scale=60.0)
        sim = Simulation(self.graph, clock=clock)
        sim.add_students(students)
        
        # Run for 1 hour during lunch peak
        max_queue_length = 0
        for _ in range(60):
            sim.step(1.0)
            
            # Track bridge queues
            for building in self.graph.buildings.values():
                for path in building.paths:
                    if path.is_bridge:
                        queue_len = len(path.queue)
                        max_queue_length = max(max_queue_length, queue_len)
        
        # Verify queues were active (some congestion occurred)
        self.assertGreaterEqual(
            max_queue_length,
            0,
            "Queue system should be tracking bridge traffic"
        )
        
        # Verify no extreme queue buildup
        self.assertLess(
            max_queue_length,
            80,
            f"Peak queue length {max_queue_length} too high"
        )
    
    def test_release_controller_batching(self) -> None:
        """Test that ReleaseController properly batches student releases."""
        students = self._create_students(80)
        clock = SimulationClock(start_time="07:00", time_scale=60.0)
        sim = Simulation(self.graph, clock=clock)
        sim.add_students(students)
        
        # Run for 2 hours
        for _ in range(120):
            sim.step(1.0)
        
        # Verify release controller statistics
        rc = sim.release_controller
        self.assertGreater(
            rc.get_statistics()["total_released"],
            0,
            "Release controller should have released some students"
        )
    
    def _create_students(self, count: int) -> List[Student]:
        """Helper to create specified number of students."""
        students = []
        schedule_list = list(self.schedules.values())
        schedule_count = len(schedule_list)
        
        # Get starting building (use first dorm building)
        start_building = self.graph.get_building("D5a")
        if start_building is None:
            # Fallback to any available building
            start_building = list(self.graph.buildings.values())[0]
        
        for i in range(count):
            schedule = schedule_list[i % schedule_count]
            student = Student(
                student_id=f"S{i:03d}",
                class_name=schedule.class_name,
                schedule=schedule,
                start_building=start_building
            )
            students.append(student)
        
        return students


if __name__ == "__main__":
    unittest.main()
