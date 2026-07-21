from src.graph import shortest_path
from .engine import SimulationState, DroneStatus
from .graph import Graph, assign_paths, cost, reconstruct_path
from .parsing import FlightNetworkParser
from .visualization import Visualizer
import sys


def main():
    parser = FlightNetworkParser()
    network = parser.parse_file(sys.argv[1])
    g = Graph(network)
    K = g.network.nb_drones
    run_simulation(g, K)


def run_simulation(g: Graph, K: int):
    sim = SimulationState(g)
    drone_paths = assign_paths(g, K)
    visualizer = Visualizer(g)
    visualizer.render(sim, "(press SPACE to start)")

    while not sim.is_done():
        proposed_moves = []
        for drone in sim.drones:
            if drone.status in (DroneStatus.DELIVERED, DroneStatus.IN_TRANSIT):
                continue
            info = drone_paths[drone.id]
            path, progress = info["path"], info["progress"]
            if progress + 1 >= len(path):
                continue
            next_hop = path[progress + 1]
            proposed_moves.append((drone.id, next_hop))
        legal_moves = sim.validate_moves(proposed_moves)
        legal_ids = {drone_id for drone_id, _ in legal_moves}

        STUCK_THRESHOLD = 3

        for drone_id, next_hop in proposed_moves:
            if drone_id in legal_ids:
                drone_paths[drone_id]["stuck_turns"] = 0
                continue

            info = drone_paths[drone_id]
            info["stuck_turns"] += 1

            if info["stuck_turns"] >= STUCK_THRESHOLD:
                drone = sim.drones[drone_id - 1]
                path, progress = info["path"], info["progress"]

                alt_dist, alt_pred = shortest_path(
                    g, start_name=drone.location,
                    blocked_edges={(drone.location, next_hop)}
                )

                if alt_dist is not None and \
                   alt_dist[g.network.end_hub.name] != float("inf"):
                    remaining_current_cost = cost(g, path[progress:])
                    alt_cost = alt_dist[g.network.end_hub.name]

                    if alt_cost <= \
                       remaining_current_cost + info["stuck_turns"]:
                        alt_path = reconstruct_path(
                            alt_pred, drone.location, g.network.end_hub.name
                        )
                        info["path"] = alt_path
                        info["progress"] = 0
                        info["stuck_turns"] = 0
        moved = sim.execute_moves(legal_moves)
        for drone_id, _ in legal_moves:
            drone_paths[drone_id]["progress"] += 1
        line = sim.format_output(moved)
        if line:
            print(line)
        visualizer.render(sim, line)
        sim.turn += 1
    return sim.turn


if __name__ == "__main__":
    main()
