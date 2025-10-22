"""Tests for bridge congestion feature."""

import unittest

from campus import (
    Building,
    Graph,
    Path,
    Schedule,
    Simulation,
    SimulationClock,
    Student,
)


class BridgeCongestionTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a simple graph with one bridge."""
        self.graph = Graph()
        
        # North side
        self.graph.add_building(Building(building_id="north", name="North Area", x=100, y=100))
        self.graph.add_building(Building(building_id="bridge_head", name="Bridge Head", x=100, y=200))
        
        # South side
        self.graph.add_building(Building(building_id="bridge_end", name="Bridge End", x=100, y=400))
        self.graph.add_building(Building(building_id="south", name="South Area", x=100, y=500))
        
        # Regular paths
        self.graph.connect_buildings("north", "bridge_head", 100, difficulty=1.0)
        self.graph.connect_buildings("bridge_end", "south", 100, difficulty=1.0)
        
        # Bridge with capacity limit
        self.bridge = self.graph.connect_buildings(
            "bridge_head", "bridge_end", 
            length=200, 
            capacity=5,  # Small capacity
            is_bridge=True,
            congestion_factor=2.0  # High congestion impact
        )

    def test_bridge_marked_correctly(self) -> None:
        """Test that bridges are marked with is_bridge flag."""
        self.assertTrue(self.bridge.is_bridge)
        self.assertEqual(self.bridge.capacity, 5)
        self.assertEqual(self.bridge.congestion_factor, 2.0)

    def test_bridge_travel_time_increases_with_congestion(self) -> None:
        """Test that bridge travel time increases as it fills up."""
        # Empty bridge
        base_time = self.bridge.get_travel_time()
        self.assertAlmostEqual(base_time, 200 / 80.0)  # 2.5 minutes
        
        # Add 3 students (60% capacity)
        self.bridge.current_students = ["s1", "s2", "s3"]
        congested_time = self.bridge.get_travel_time()
        expected_time = base_time * (1.0 + 2.0 * 0.6)  # congestion_factor=2.0
        self.assertAlmostEqual(congested_time, expected_time)
        self.assertGreater(congested_time, base_time)
        
        # Full bridge (100% capacity)
        self.bridge.current_students = ["s1", "s2", "s3", "s4", "s5"]
        full_time = self.bridge.get_travel_time()
        expected_full = base_time * (1.0 + 2.0 * 1.0)  # Triple time when full
        self.assertAlmostEqual(full_time, expected_full)
        self.assertGreater(full_time, congested_time)

    def test_congestion_level_reporting(self) -> None:
        """Test get_congestion_level() method."""
        self.bridge.current_students = []
        self.assertEqual(self.bridge.get_congestion_level(), 'clear')
        
        self.bridge.current_students = ["s1", "s2"]  # 40%
        self.assertEqual(self.bridge.get_congestion_level(), 'moderate')
        
        self.bridge.current_students = ["s1", "s2", "s3", "s4"]  # 80%
        self.assertEqual(self.bridge.get_congestion_level(), 'heavy')
        
        self.bridge.current_students = ["s1", "s2", "s3", "s4", "s5"]  # 100%
        self.assertEqual(self.bridge.get_congestion_level(), 'full')

    def test_student_waits_at_congested_bridge(self) -> None:
        """Test that students wait when bridge is too congested."""
        schedule = Schedule("TestClass")
        schedule.add_event("08:00", "south")
        
        student = Student("test-1", "TestClass", schedule, self.graph.buildings["north"])
        
        # Plan route
        student.plan_next_move("07:00", self.graph)
        self.assertEqual(student.state, "moving")
        
        # Fill the bridge to trigger congestion
        self.bridge.current_students = ["other1", "other2", "other3", "other4"]  # 80% full
        
        # Student arrives at bridge head
        # Move through first segment (north to bridge_head)
        first_segment_time = self.graph.get_path("north", "bridge_head").get_travel_time()
        student.update(first_segment_time)
        
        self.assertEqual(student.current_location.building_id, "bridge_head")
        
        # Try to enter congested bridge - should switch to waiting
        student.update(0.1)
        self.assertEqual(student.state, "waiting")

    def test_student_resumes_when_congestion_clears(self) -> None:
        """Test that waiting students resume when bridge clears."""
        schedule = Schedule("TestClass")
        schedule.add_event("08:00", "south")
        
        student = Student("test-1", "TestClass", schedule, self.graph.buildings["bridge_head"])
        student.plan_next_move("07:00", self.graph)
        
        # Fill bridge
        self.bridge.current_students = ["other1", "other2", "other3", "other4"]
        
        # Student tries to enter and waits
        student.update(0.1)
        self.assertEqual(student.state, "waiting")
        
        # Clear the bridge
        self.bridge.current_students = ["other1"]  # Now only 20% full
        
        # Student should resume
        student.update(0.1)
        self.assertEqual(student.state, "moving")

    def test_large_bridge_has_no_congestion_effect(self) -> None:
        """Test that large bridges (capacity=None) have fixed travel time."""
        large_bridge = self.graph.connect_buildings(
            "south", "north",
            length=200,
            capacity=None,  # Unlimited
            is_bridge=True,
            congestion_factor=1.0
        )
        
        base_time = large_bridge.get_travel_time()
        
        # Add many students
        large_bridge.current_students = [f"s{i}" for i in range(100)]
        
        # Time should not change
        congested_time = large_bridge.get_travel_time()
        self.assertAlmostEqual(base_time, congested_time)
        
        # Always reports clear
        self.assertEqual(large_bridge.get_congestion_level(), 'clear')


if __name__ == "__main__":
    unittest.main()
