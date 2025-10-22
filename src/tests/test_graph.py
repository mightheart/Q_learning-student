"""Unit tests for the graph data structures."""

import unittest

from campus import Building, Graph


class GraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        for idx, name, x, y in (
            ("A", "Gate", 0, 0),
            ("B", "Library", 100, 0),
            ("C", "Cafeteria", 200, 0),
            ("D", "Gym", 100, 100),
        ):
            self.graph.add_building(Building(building_id=idx, name=name, x=x, y=y))

        self.graph.connect_buildings("A", "B", length=80)
        self.graph.connect_buildings("B", "C", length=40)
        self.graph.connect_buildings("A", "D", length=60, difficulty=1.2)
        self.graph.connect_buildings("D", "C", length=60)

    def test_shortest_path_prefers_lower_time(self) -> None:
        total_time, route = self.graph.find_shortest_path("A", "C")
        names = [building.name for building in route]
        self.assertEqual(names, ["Gate", "Library", "Cafeteria"])
        self.assertAlmostEqual(total_time, (80 + 40) / 80.0)

    def test_capacity_restrictions_block_edges(self) -> None:
        direct = self.graph.connect_buildings("A", "C", length=50, difficulty=1.0, capacity=1)
        direct.current_students.append("student-1")
        total_time, route = self.graph.find_shortest_path("A", "C")
        self.assertGreater(total_time, direct.get_travel_time())
        self.assertNotIn("Cafeteria", [building.name for building in route[:2]])

    def test_raises_when_no_route(self) -> None:
        isolated = Building(building_id="X", name="Dorm", x=300, y=300)
        self.graph.add_building(isolated)
        with self.assertRaises(ValueError):
            self.graph.find_shortest_path("A", "X")


if __name__ == "__main__":
    unittest.main()
