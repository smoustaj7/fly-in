from .parsing import FlightNetworkParser, FlightNetwork
import sys


class Engine:
    def __init__(self, network: FlightNetwork):
        self.network = network
        self.drones: list[Drone] = []

    def run_turn(self):
        pass

    def update_drones(self):
        pass


class Drone:
    def __init__(self, id: int, zone: str, network: FlightNetwork):
        self.id = id
        self.zone = zone
        self.network = network

    def move(self):
        pass

    def next_zone(self):
        pass


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 -m src <map_file>")
        sys.exit(1)
    network = FlightNetworkParser.parse_file(sys.argv[1])
    engine = Engine(network)        

if __name__ == '__main__':
    main()
