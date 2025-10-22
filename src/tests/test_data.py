"""Tests for campus data creation."""

import unittest

from campus import create_campus_map, create_class_schedules


class CampusDataTests(unittest.TestCase):
    def test_campus_map_has_required_buildings(self) -> None:
        graph = create_campus_map()
        self.assertGreaterEqual(len(graph.buildings), 20)  # New design has 20 buildings
        # Test teaching buildings
        self.assertIn("D3a", graph.buildings)
        self.assertIn("F3d", graph.buildings)
        # Test library
        self.assertIn("library", graph.buildings)
        # Test dorms
        self.assertIn("D5a", graph.buildings)
        self.assertIn("D5d", graph.buildings)
        # Test facilities
        self.assertIn("canteen", graph.buildings)
        self.assertIn("gym", graph.buildings)

    def test_all_buildings_have_paths(self) -> None:
        graph = create_campus_map()
        for building in graph.buildings.values():
            self.assertGreater(
                len(building.paths),
                0,
                f"Building {building.name} has no paths",
            )

    def test_class_schedules_created(self) -> None:
        schedules = create_class_schedules()
        self.assertEqual(len(schedules), 5)
        self.assertIn("CS1", schedules)
        self.assertIn("MATH", schedules)

    def test_each_schedule_has_events(self) -> None:
        schedules = create_class_schedules()
        for class_code, schedule in schedules.items():
            self.assertGreater(
                len(schedule),
                0,
                f"Schedule {class_code} has no events",
            )


if __name__ == "__main__":
    unittest.main()
