"""Tests covering schedule and student behaviour."""

import unittest

from campus import (
    Building,
    Graph,
    Schedule,
    ScheduleEvent,
    Student,
)


class ScheduleTests(unittest.TestCase):
    def test_next_event_is_strictly_after_current_time(self) -> None:
        schedule = Schedule("ClassA")
        schedule.add_event("07:30", "A")
        schedule.add_event("08:00", "B")
        first = schedule.get_next_event("07:00")
        self.assertIsNotNone(first)
        if first is not None:
            self.assertEqual(first.time_str, "07:30")
        second = schedule.get_next_event("07:45")
        self.assertIsNotNone(second)
        if second is not None:
            self.assertEqual(second.time_str, "08:00")
        self.assertIsNone(schedule.get_next_event("09:00"))


class StudentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        for idx, name, x, y in (
            ("A", "Gate", 0, 0),
            ("B", "Library", 100, 0),
            ("C", "Hall", 200, 0),
        ):
            self.graph.add_building(Building(building_id=idx, name=name, x=x, y=y))

        self.graph.connect_buildings("A", "B", length=80, difficulty=1.0)
        self.graph.connect_buildings("B", "C", length=50, difficulty=1.0)

    def test_student_plans_and_arrives(self) -> None:
        schedule = Schedule("ClassA")
        schedule.add_event("08:00", "B")
        student = Student("stu-1", "ClassA", schedule, self.graph.buildings["A"])

        student.plan_next_move("07:30", self.graph)
        self.assertEqual(student.state, "moving")
        self.assertEqual(student.path_to_destination[-1].building_id, "B")

        total_time, _ = self.graph.find_shortest_path("A", "B")
        student.update(total_time)
        self.assertEqual(student.current_location.building_id, "B")
        self.assertEqual(student.state, "in_class")

    def test_capacity_limits_block_additional_students(self) -> None:
        self.graph.connect_buildings("A", "C", length=60, capacity=1)
        schedule = Schedule("ClassA")
        schedule.add_event("08:00", "C")
        student_one = Student("stu-1", "ClassA", schedule, self.graph.buildings["A"])
        student_two = Student("stu-2", "ClassA", schedule, self.graph.buildings["A"])

        student_one.plan_next_move("07:30", self.graph)
        student_one.update(0.1)  # start occupying the path with capacity

        student_two.plan_next_move("07:30", self.graph)
        self.assertEqual(student_two.path_to_destination[1].building_id, "B")


if __name__ == "__main__":
    unittest.main()
