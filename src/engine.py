from .parsing import FlightNetwork
from enum import Enum
from .graph import Graph


class DroneStatus(Enum):
    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class Drone:
    def __init__(self, drone_id: int, start_zone: str):
        self.id = drone_id
        self.status = DroneStatus.WAITING
        self.location = start_zone
        self.destination = None
        self.arrival_turn = None

    def __repr__(self):
        return f"Drone(id={self.id}, status={self.status.value}," \
            f" location={self.location})"


class SimulationState:
    def __init__(self, g: Graph):
        self.graph = g
        self.turn = 0
        self.reservations = {}

        start_name = g.network.start_hub.name
        self.drones = [
            Drone(drone_id=i, start_zone=start_name)
            for i in range(1, g.network.nb_drones + 1)
        ]

        self.zone_occupancy = {}
        self.zone_occupancy[start_name] = g.network.nb_drones
        for zone in g.graph:
            if zone != start_name:
                self.zone_occupancy[zone] = 0

    def can_enter_zone(self, zone_name: str, proposed_moves: list[any])\
            -> bool:
        max_drones = self.graph.graph[zone_name]["node"]["max_drones"]

        if max_drones is None:
            return True

        current_occupancy = self.zone_occupancy[zone_name]
        departing_count = 0
        for move in proposed_moves:
            if move[1] != zone_name and \
                    self.drones[move[0] - 1].location == zone_name:
                departing_count += 1

        entering_count = 0
        for move in proposed_moves:
            if move[1] == zone_name and \
                    self.drones[move[0] - 1].location != zone_name:
                entering_count += 1

        return current_occupancy - departing_count + entering_count <= \
            max_drones

    def can_use_connection(
        self, from_zone: str, to_zone: str, proposed_moves: list[any]
    ) -> bool:
        for zone in self.graph.graph[from_zone]["edges"]:
            if zone[0] == to_zone:
                max_link_capacity = zone[3]
                break

        usage_count = 0
        for m in proposed_moves:
            if m[1] == to_zone and \
                    self.drones[m[0] - 1].location == from_zone:
                usage_count += 1

        return usage_count <= max_link_capacity

    def reserve_arrival(self, zone_name: str, arrival_turn: int) -> bool:
        if arrival_turn not in self.reservations:
            self.reservations[arrival_turn] = {}
        if zone_name not in self.reservations[arrival_turn]:
            self.reservations[arrival_turn][zone_name] = 0

        if self.graph.graph[zone_name]["node"]["max_drones"] is None or \
                self.reservations[arrival_turn][zone_name] < \
                self.graph.graph[zone_name]["node"]["max_drones"]:
            self.reservations[arrival_turn][zone_name] += 1
            return True
        return False


class Engine:
    def __init__(self, network: FlightNetwork):
        self.network = network
        self.drones: list[Drone] = []

    def run_turn(self):
        pass

    def update_drones(self):
        pass
