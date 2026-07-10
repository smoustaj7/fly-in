from parsing import FlightNetworkParser
import sys


class Graph:
    def __init__(self, network: FlightNetworkParser):
        self.network = network
        self.graph = self.build_graph()

    def build_graph(self):
        graph = {}
        for hub in self.network.hubs:
            if hub.zone != "blocked":
                is_start = hub.name == self.network.start_hub.name
                is_end = hub.name == self.network.end_hub.name
                graph[hub.name] = {
                    "node": {
                        "zone": hub.zone,
                        "max_drones": None if (is_start or is_end)
                        else hub.max_drones,
                        "is_start": is_start,
                        "is_end": is_end,
                    },
                    "edges": [],
                }

        hub_lookup = {hub.name: hub for hub in self.network.hubs}

        for conn in self.network.connections:
            source = hub_lookup[conn.hub1]
            dest = hub_lookup[conn.hub2]

            if source.zone == "blocked" or dest.zone == "blocked":
                continue

            cost_to_dest = 1 if dest.zone in ("normal", "priority") else 2
            graph[conn.hub1]["edges"].append(
                [
                    conn.hub2,
                    dest.zone,
                    cost_to_dest,
                    conn.max_link_capacity,
                ]
            )

            cost_to_source = 1 if source.zone in ("normal", "priority") else 2
            graph[conn.hub2]["edges"].append(
                [
                    conn.hub1,
                    source.zone,
                    cost_to_source,
                    conn.max_link_capacity,
                ]
            )
        return graph


g = Graph(FlightNetworkParser.parse_file(sys.argv[1]))
print(g.graph)