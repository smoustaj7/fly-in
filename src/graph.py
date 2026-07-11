from parsing import FlightNetworkParser
import sys
from collections import deque
from heapq import heappush, heappop


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

    def is_end_reachable(self) -> bool:
        start = self.network.start_hub.name
        end = self.network.end_hub.name

        visited = {start}
        queue = deque([start])

        while queue:
            curr = queue.popleft()
            if curr == end:
                return True
            for edge in self.graph[curr]["edges"]:
                neighbor = edge[0]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False


def shortest_path(g: Graph):
    distance = {hub: float("inf") for hub in g.graph}
    distance[g.network.start_hub.name] = 0
    curr = g.network.start_hub.name
    predecessor = {hub: None for hub in g.graph}
    visited = set()
    pq = [(0, curr)]
    if not g.is_end_reachable():
        return None, None
    while curr != g.network.end_hub.name:
        if curr in visited:
            curr = heappop(pq)[1]
            continue
        for edge in g.graph[curr]["edges"]:
            neighbor, zone_type, cost, capacity = edge
            new_dist = distance[curr] + cost
            if new_dist < distance[neighbor] and neighbor not in visited:
                distance[neighbor] = new_dist
                predecessor[neighbor] = curr
                heappush(pq, (new_dist, neighbor))
        visited.add(curr)
        curr = heappop(pq)[1]
    return distance, predecessor


def reconstruct_path(predecessor, start, end):
    path = []
    curr = end
    if predecessor[end] is None and end != start:
        return None
    while curr != start:
        path.append(curr)
        curr = predecessor[curr]
    path.append(start)
    path.reverse()
    return path
