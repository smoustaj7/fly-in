from parsing import FlightNetworkParser
from collections import deque
from heapq import heappush, heappop
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

    def is_end_reachable(
        self,
        start_name,
        end_name,
        blocked_nodes=None,
        blocked_edges=None
    ) -> bool:
        blocked_nodes = blocked_nodes or set()
        blocked_edges = blocked_edges or set()
        visited = {start_name}
        queue = deque([start_name])

        while queue:
            curr = queue.popleft()
            if curr == end_name:
                return True
            for edge in self.graph[curr]["edges"]:
                neighbor = edge[0]
                if neighbor not in visited \
                   and (curr, neighbor) not in blocked_edges \
                   and neighbor not in blocked_nodes:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def find_bottlenecks(self):
        start = self.network.start_hub.name
        end = self.network.end_hub.name
        bottlenecks = []

        for node in self.graph:
            if node == start or node == end:
                continue
            if not self.is_end_reachable(start, end, blocked_nodes={node}):
                bottlenecks.append(node)
        return bottlenecks


def shortest_path(
    g: Graph,
    start_name=None,
    blocked_edges=None,
    blocked_nodes=None
) -> tuple[dict[str, float], dict[str, str]]:

    start_name = start_name or g.network.start_hub.name
    blocked_edges = blocked_edges or set()
    blocked_nodes = blocked_nodes or set()
    distance = {hub: float("inf") for hub in g.graph}
    distance[start_name] = 0
    curr = start_name
    predecessor = {hub: None for hub in g.graph}
    visited = set()
    pq = [(0, curr)]
    if not g.is_end_reachable(
        start_name,
        g.network.end_hub.name,
        blocked_nodes,
        blocked_edges
    ):
        return None, None
    while curr != g.network.end_hub.name:
        if curr in visited or curr in blocked_nodes:
            curr = heappop(pq)[1]
            continue
        for edge in g.graph[curr]["edges"]:
            neighbor, zone_type, cost, capacity = edge
            new_dist = distance[curr] + cost
            if new_dist < distance[neighbor] and neighbor not in visited \
               and (curr, neighbor) not in blocked_edges \
               and neighbor not in blocked_nodes:
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


def cost(g: Graph, path):
    total = 0
    for i in range(len(path) - 1):
        curr_name = path[i]
        next_name = path[i + 1]
        for edge in g.graph[curr_name]["edges"]:
            neighbor, zone_type, cost, capacity = edge
            if neighbor == next_name:
                total += cost
                break
    return total


def k_shortest_paths(g: Graph, K: int):
    dist, pred = shortest_path(g)
    if dist is None:
        return []

    start = g.network.start_hub.name
    end = g.network.end_hub.name
    first_path = reconstruct_path(pred, start, end)
    A = [(dist[end], first_path)]
    B = []

    for _ in range(1, K):
        prev_cost, prev_path = A[-1]
        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[:i + 1]
            blocked_edges = set()
            for path_cost, path in A:
                if len(path) > i and path[:i + 1] == root_path:
                    blocked_edges.add((path[i], path[i + 1]))
            blocked_nodes = set()
            for node in root_path[:-1]:
                blocked_nodes.add(node)
            spur_dist, spur_pred = shortest_path(
                g, start_name=spur_node,
                blocked_edges=blocked_edges,
                blocked_nodes=blocked_nodes
            )
            if spur_dist is None or spur_dist[end] == float("inf"):
                continue
            spur_path = reconstruct_path(spur_pred, spur_node, end)
            total_path = root_path[:-1] + spur_path
            root_cost = cost(g, root_path)
            total_cost = root_cost + spur_dist[end]
            candidate = (total_cost, total_path)
            if candidate not in B and candidate not in A:
                heappush(B, candidate)
        if not B:
            break
        B.sort(key=lambda x: x[0])
        A.append(heappop(B))
    return A

