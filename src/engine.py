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

        return current_occupancy - departing_count + entering_count + \
            self.reservations.get(self.turn, {}).get(zone_name, 0) \
            <= max_drones

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

    def validate_moves(self, proposed_moves: list) -> list:
        legal_moves = []

        for move in proposed_moves:
            drone_id, destination = move
            origin = self.drones[drone_id - 1].location
            zone_type = None
            for edge in self.graph.graph[origin]["edges"]:
                if edge[0] == destination:
                    zone_type = edge[1]
                    break
            if zone_type is None:
                continue

            candidate_batch = legal_moves + [move]

            if not self.can_use_connection(
                origin, destination, candidate_batch
            ):
                continue
            if zone_type == "restricted":
                if not self.reserve_arrival(destination, self.turn + 2):
                    continue
            else:
                if not self.can_enter_zone(destination, candidate_batch):
                    continue
            legal_moves.append(move)

        return legal_moves

    def execute_moves(self, legal_moves: list) -> str:
        moved = []
        for drone_id, destination in legal_moves:
            drone = self.drones[drone_id - 1]
            if self.graph.graph[destination]["node"]["zone"] == "restricted":
                self.zone_occupancy[drone.location] -= 1
                drone.status = DroneStatus.IN_TRANSIT
                drone.location = drone.location + "-" + destination
                drone.destination = destination
                drone.arrival_turn = self.turn + 2
            else:
                self.zone_occupancy[destination] += 1
                self.zone_occupancy[drone.location] -= 1
                if destination == self.graph.network.end_hub.name:
                    drone.status = DroneStatus.DELIVERED
                else:
                    drone.status = DroneStatus.MOVING
                drone.location = destination
                moved.append((drone.id, drone.location))
        for drone in self.drones:
            if drone.status == DroneStatus.IN_TRANSIT \
                    and drone.arrival_turn == self.turn:
                if drone.destination == self.graph.network.end_hub.name:
                    drone.status = DroneStatus.DELIVERED
                else:
                    drone.status = DroneStatus.MOVING
                drone.location = drone.destination
                self.zone_occupancy[drone.location] += 1
                drone.destination = None
                drone.arrival_turn = None
                moved.append((drone.id, drone.location))
        return moved

    def format_output(self, moved: list) -> str:
        output = []
        for drone_id, location in moved:
            output.append(f"D{drone_id}-{location}")
        return " ".join(output)

    def is_done(self) -> bool:
        for drone in self.drones:
            if drone.status != DroneStatus.DELIVERED:
                return False
        return True