from .parsing import FlightNetworkParser, FlightNetwork
import sys


class Graph:
    def __init__(self, network: FlightNetwork):
        self.network = network
        self.graph = self.build_graph()

    def build_graph(self):
        graph = {}
        for hub in self.network.hubs:
            if hub.zone != "blocked":
                graph[hub.name] = []

        hub_lookup = {hub.name: hub for hub in self.network.hubs}

        for conn in self.network.connections:
            source = hub_lookup[conn.hub1]
            dest = hub_lookup[conn.hub2]

            if source.zone == "blocked" or dest.zone == "blocked":
                continue

            cost = 1 if dest.zone in ("normal", "priority") else 2
            graph[conn.hub1].append(
                [conn.hub2, cost, conn.max_link_capacity, dest.max_drones]
            )
        return graph


g = Graph(FlightNetworkParser.parse_file(sys.argv[1]))
print(g.graph)
