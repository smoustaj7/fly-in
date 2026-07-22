from collections import deque
from heapq import heappop, heappush
from typing import Any, Optional

from .parsing import FlightNetwork


class Graph:
    def __init__(self, network: FlightNetwork):
        self.network = network
        self.hubs: list[Any] = list(network.hubs)
        self.graph: dict[str, dict[str, Any]] = self.build_graph()

    def build_graph(self) -> dict[str, dict[str, Any]]:
        graph: dict[str, dict[str, Any]] = {}
        start_hub = self.network.start_hub
        end_hub = self.network.end_hub
        if start_hub is None or end_hub is None:
            raise ValueError("Network must define start and end hubs")

        for hub in self.network.hubs:
            if hub.zone != "blocked":
                is_start = hub.name == start_hub.name
                is_end = hub.name == end_hub.name
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
        start_name: str,
        end_name: str,
        blocked_nodes: Optional[set[str]] = None,
        blocked_edges: Optional[set[tuple[str, str]]] = None
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

    def find_bottlenecks(self) -> list[str]:
        start_hub = self.network.start_hub
        end_hub = self.network.end_hub
        if start_hub is None or end_hub is None:
            return []
        start = start_hub.name
        end = end_hub.name
        bottlenecks: list[str] = []

        for node in self.graph:
            if node == start or node == end:
                continue
            if not self.is_end_reachable(start, end, blocked_nodes={node}):
                bottlenecks.append(node)
        return bottlenecks


def shortest_path(
    g: Graph,
    start_name: Optional[str] = None,
    blocked_edges: Optional[set[tuple[str, str]]] = None,
    blocked_nodes: Optional[set[str]] = None
) -> tuple[dict[str, float] | None, dict[str, Optional[str]] | None]:
    start_hub = g.network.start_hub
    end_hub = g.network.end_hub
    if start_hub is None or end_hub is None:
        return None, None

    start_name = start_name or start_hub.name
    blocked_edges = blocked_edges or set()
    blocked_nodes = blocked_nodes or set()
    distance: dict[str, float] = {hub: float("inf") for hub in g.graph}
    distance[start_name] = 0
    curr = start_name
    predecessor: dict[str, Optional[str]] = {hub: None for hub in g.graph}
    visited: set[str] = set()
    pq: list[tuple[float, str]] = [(0.0, curr)]
    if not g.is_end_reachable(
        start_name,
        end_hub.name,
        blocked_nodes,
        blocked_edges
    ):
        return None, None
    while curr != end_hub.name:
        if curr in visited or curr in blocked_nodes:
            if not pq:
                return None, None
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
        if not pq:
            return None, None
        curr = heappop(pq)[1]
    return distance, predecessor


def reconstruct_path(
    predecessor: dict[str, Optional[str]],
    start: str,
    end: str
) -> Optional[list[str]]:
    path: list[str] = []
    curr = end
    if predecessor.get(end) is None and end != start:
        return None
    while curr != start:
        path.append(curr)
        prev = predecessor.get(curr)
        if prev is None:
            return None
        curr = prev
    path.append(start)
    path.reverse()
    return path


def cost(g: Graph, path: list[str]) -> int:
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


def k_shortest_paths(g: Graph, K: int) -> list[tuple[float, list[str]]]:
    dist, pred = shortest_path(g)
    if dist is None or pred is None:
        return []

    start = g.network.start_hub.name if g.network.start_hub is not None else ""
    end = g.network.end_hub.name if g.network.end_hub is not None else ""
    first_path = reconstruct_path(pred, start, end)
    if first_path is None:
        return []
    A: list[tuple[float, list[str]]] = [(dist[end], first_path)]
    B: list[tuple[float, list[str]]] = []

    for _ in range(1, K):
        _, prev_path = A[-1]
        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[:i + 1]
            blocked_edges: set[tuple[str, str]] = set()
            for _, path in A:
                if len(path) > i and path[:i + 1] == root_path:
                    blocked_edges.add((path[i], path[i + 1]))
            blocked_nodes: set[str] = set()
            for node in root_path[:-1]:
                blocked_nodes.add(node)
            spur_dist, spur_pred = shortest_path(
                g,
                start_name=spur_node,
                blocked_edges=blocked_edges,
                blocked_nodes=blocked_nodes
            )
            if spur_dist is None or spur_pred \
                    is None or spur_dist[end] == float("inf"):
                continue
            spur_path = reconstruct_path(spur_pred, spur_node, end)
            if spur_path is None:
                continue
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


def assign_paths(g: Graph, K: int) -> dict[int, dict[str, Any]]:
    paths = k_shortest_paths(g, K)
    if not paths:
        return {}
    drone_paths: dict[int, dict[str, Any]] = {}
    for d in range(1, g.network.nb_drones + 1):
        drone_paths[d] = {
            "path": paths[d % len(paths)][1],
            "progress": 0,
            "stuck_turns": 0
        }
    return drone_paths
