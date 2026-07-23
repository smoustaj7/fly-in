import unittest
from src.parsing import FlightNetworkParser


class TestFlightNetworkParserErrorHandling(unittest.TestCase):

    def test_malformed_files(self) -> None:
        # Missing drone count
        data_missing_drones = """
start_hub: start 0 0 [color=green]
end_hub: goal 1 0 [color=red]
connection: start-goal
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_missing_drones)
        self.assertIn("Invalid nb_drones", str(ctx.exception))

        # Invalid drone count format
        data_invalid_drones = """
nb_drones: abc
start_hub: start 0 0 [color=green]
end_hub: goal 1 0 [color=red]
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_invalid_drones)
        self.assertIn("nb_drones", str(ctx.exception))

        # Missing colon
        data_missing_colon = """
nb_drones: 2
start_hub start 0 0
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_missing_colon)
        self.assertIn("Missing colon", str(ctx.exception))

    def test_invalid_zone_types(self) -> None:
        data_invalid_zone = """
nb_drones: 1
start_hub: start 0 0 [color=green]
hub: mid 1 0 [zone=hyper_zone]
end_hub: goal 2 0 [color=red]
connection: start-mid
connection: mid-goal
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_invalid_zone)
        self.assertIn("invalid zone type: 'hyper_zone'", str(ctx.exception))

    def test_missing_start_or_end_hub(self) -> None:
        # Missing start_hub
        data_no_start = """
nb_drones: 1
end_hub: goal 1 0 [color=red]
hub: start 0 0
connection: start-goal
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_no_start)
        self.assertIn("Start hub is not defined", str(ctx.exception))

        # Missing end_hub
        data_no_end = """
nb_drones: 1
start_hub: start 0 0 [color=green]
connection: start-goal
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_no_end)
        self.assertIn("End hub is not defined", str(ctx.exception))

    def test_invalid_capacity_values(self) -> None:
        # Non-positive max_drones
        data_invalid_max_drones = """
nb_drones: 1
start_hub: start 0 0
hub: node1 1 0 [max_drones=0]
end_hub: goal 2 0
connection: start-node1
connection: node1-goal
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_invalid_max_drones)
        self.assertIn("invalid max_drones", str(ctx.exception))

        # Non-positive max_link_capacity
        data_invalid_capacity = """
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal [max_link_capacity=-1]
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_invalid_capacity)
        self.assertIn("invalid max_link_capacity", str(ctx.exception))

    def test_duplicate_zone_names_or_connections(self) -> None:
        # Duplicate zone names
        data_dup_zone = """
nb_drones: 1
start_hub: start 0 0
hub: start 1 0
end_hub: goal 2 0
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_dup_zone)
        self.assertIn("Duplicate hub name", str(ctx.exception))

        # Duplicate connection
        data_dup_conn = """
nb_drones: 1
start_hub: start 0 0
end_hub: goal 1 0
connection: start-goal
connection: goal-start
"""
        with self.assertRaises(ValueError) as ctx:
            FlightNetworkParser.parse_string(data_dup_conn)
        self.assertIn("Duplicate connection", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
