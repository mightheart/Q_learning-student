"""Tests for the simulation clock and engine."""

import unittest

from campus import (
    Building,
    Graph,
    Schedule,
    Simulation,
    SimulationClock,
    Student,
)


class SimulationClockTests(unittest.TestCase):
    def test_tick_advances_time_with_scale(self) -> None:
        clock = SimulationClock(start_time="07:00", time_scale=2.0)
        progressed = clock.tick(30.0)
        self.assertAlmostEqual(progressed, 1.0)
        self.assertEqual(clock.current_time_str, "07:01")
        self.assertGreater(clock.current_minutes, 7 * 60)

    def test_tick_rejects_negative_seconds(self) -> None:
        clock = SimulationClock()
        with self.assertRaises(ValueError):
            clock.tick(-1.0)


class SimulationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        for idx, name, x, y in (
            ("A", "Gate", 0, 0),
            ("B", "Library", 80, 0),
        ):
            self.graph.add_building(Building(building_id=idx, name=name, x=x, y=y))
        self.graph.connect_buildings("A", "B", length=80, difficulty=1.0)

    def test_student_arrival_adds_event_log(self) -> None:
        schedule = Schedule("ClassA")
        schedule.add_event("07:30", "B")
        student = Student("stu-1", "ClassA", schedule, self.graph.get_building("A"))

        clock = SimulationClock(start_time="07:00", time_scale=60.0)
        simulation = Simulation(self.graph, clock=clock)
        simulation.add_students([student])

        # Step once with one real second => one simulated minute due to scale.
        simulation.step(1.0)

        self.assertEqual(student.current_location.building_id, "B")
        self.assertEqual(student.state, "in_class")
        self.assertEqual(len(simulation.event_log), 1)
        event = simulation.event_log[0]
        self.assertEqual(event.student_id, "stu-1")
        self.assertIn("Library", event.description)
        self.assertEqual(event.timestamp, simulation.clock.current_time_str)


if __name__ == "__main__":
    unittest.main()
