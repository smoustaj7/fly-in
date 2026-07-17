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


class Engine:
    def __init__(self, network: FlightNetwork):
        self.network = network
        self.drones: list[Drone] = []

    def run_turn(self):
        pass

    def update_drones(self):
        pass
