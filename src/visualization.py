import sys
import os
import pygame

# Add project root to path so we can resolve 'src' imports when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parsing import FlightNetworkParser
from src.graph import Graph, assign_paths
from src.engine import SimulationState, DroneStatus

ZONE_TYPE_COLORS = {
    "normal": pygame.Color("forestgreen"),
    "blocked": pygame.Color("red"),
    "restricted": pygame.Color("gold"),
    "priority": pygame.Color("cyan"),
}

BACKGROUND = pygame.Color("skyblue3")
CLOUD_COLOR = pygame.Color(255, 255, 255, 180)
HEADER_BG = pygame.Color("gray20")
EDGE_COLOR = pygame.Color("gray30")
TEXT_COLOR = pygame.Color("black")
DRONE_COLOR = pygame.Color("black")
DRONE_ID_COLOR = pygame.Color("yellow")

MARGIN = 60
ZONE_RADIUS = 16
DRONE_RADIUS = 9
HEADER_HEIGHT = 34
LABEL_BG = pygame.Color(235, 235, 235)

TARGET_WIDTH = 1400
TARGET_HEIGHT = 850


def compute_scale(network):
    xs = [hub.x for hub in network.hubs]
    ys = [hub.y for hub in network.hubs]
    x_range = max(xs) - min(xs) or 1
    y_range = max(ys) - min(ys) or 1
    scale_x = (TARGET_WIDTH - 2 * MARGIN) / x_range
    scale_y = (TARGET_HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / y_range
    return min(scale_x, scale_y, 100)  # cap at 100 so small maps don't get absurdly huge


def get_zone_color(hub_name, network):
    hub = next(h for h in network.hubs if h.name == hub_name)
    if hub.color:
        try:
            return pygame.Color(hub.color)
        except ValueError:
            pass  # fall through to zone-type default
    return ZONE_TYPE_COLORS.get(hub.zone, pygame.Color("gray"))


def compute_positions(network, scale):
    xs = [hub.x for hub in network.hubs]
    ys = [hub.y for hub in network.hubs]
    min_x, min_y = min(xs), min(ys)

    positions = {}
    for hub in network.hubs:
        positions[hub.name] = (
            int((hub.x - min_x) * scale) + MARGIN,
            int((hub.y - min_y) * scale) + MARGIN + HEADER_HEIGHT,
        )
    return positions


def draw_clouds(screen, width, height):
    # A handful of simple fixed cloud shapes (clusters of overlapping circles),
    # scattered proportionally to the screen size so they scale with the map.
    cloud_specs = [
        (0.08, 0.10, 1.0), (0.32, 0.06, 0.8), (0.60, 0.12, 1.1),
        (0.80, 0.05, 0.7), (0.18, 0.20, 0.6), (0.48, 0.18, 0.9),
    ]
    for fx, fy, size in cloud_specs:
        cx, cy = int(width * fx), int(height * fy) + HEADER_HEIGHT + 20
        r = int(18 * size)
        puffs = [(0, 0), (r, 4), (-r, 4), (r // 2, -r // 3), (-r // 2, -r // 3)]
        for dx, dy in puffs:
            pygame.draw.circle(screen, CLOUD_COLOR, (cx + dx, cy + dy), int(r * 0.9))


def compute_label_sides(network):
    # Alternate label placement (above/below) per hub so adjacent
    # zone-name labels don't collide as often.
    sides = {}
    for i, hub in enumerate(network.hubs):
        sides[hub.name] = "above" if i % 2 == 0 else "below"
    return sides


def draw_frame(screen, font, id_font, g, sim, positions, label_sides, turn_line):
    screen.fill(BACKGROUND)
    draw_clouds(screen, screen.get_width(), screen.get_height())

    # Draw edges first, so zone circles sit on top
    for zone_name, data in g.graph.items():
        for edge in data["edges"]:
            neighbor = edge[0]
            if neighbor in positions:
                pygame.draw.line(screen, EDGE_COLOR,
                                  positions[zone_name], positions[neighbor], 1)

    # Draw zones with alternating label placement to reduce overlap
    for zone_name in g.graph:
        pos = positions[zone_name]
        color = get_zone_color(zone_name, g.network)
        pygame.draw.circle(screen, color, pos, ZONE_RADIUS)
        pygame.draw.circle(screen, pygame.Color("gray5"), pos, ZONE_RADIUS, 2)

        label = font.render(zone_name, True, TEXT_COLOR)
        label_x = pos[0] - label.get_width() // 2
        if label_sides[zone_name] == "above":
            label_y = pos[1] - ZONE_RADIUS - label.get_height() - 3
        else:
            label_y = pos[1] + ZONE_RADIUS + 3

        bg_rect = pygame.Rect(label_x - 3, label_y - 1,
                               label.get_width() + 6, label.get_height() + 2)
        pygame.draw.rect(screen, LABEL_BG, bg_rect, border_radius=3)
        screen.blit(label, (label_x, label_y))

    # Draw drones -- black, larger, with a bright ID for visibility.
    # In-transit drones render at the midpoint of their connection;
    # multiple drones sharing a zone are fanned out so they don't overlap.
    zone_drone_count = {}
    for drone in sim.drones:
        if drone.status == DroneStatus.DELIVERED:
            continue

        if drone.status == DroneStatus.IN_TRANSIT:
            origin, dest = drone.location.rsplit("-", 1)
            if origin not in positions or dest not in positions:
                continue
            ox, oy = positions[origin]
            dx, dy = positions[dest]
            drone_pos = ((ox + dx) // 2, (oy + dy) // 2)
        else:
            loc = drone.location
            if loc not in positions:
                continue
            pos = positions[loc]
            count = zone_drone_count.get(loc, 0)
            offset_x = (count % 3) * 14 - 14
            offset_y = (count // 3) * 14 - 14
            zone_drone_count[loc] = count + 1
            drone_pos = (pos[0] + offset_x, pos[1] + offset_y)

        pygame.draw.circle(screen, DRONE_COLOR, drone_pos, DRONE_RADIUS)
        pygame.draw.circle(screen, DRONE_ID_COLOR, drone_pos, DRONE_RADIUS, 2)

        id_label = id_font.render(str(drone.id), True, DRONE_ID_COLOR)
        screen.blit(id_label, (drone_pos[0] - id_label.get_width() // 2,
                                drone_pos[1] - id_label.get_height() // 2))

    # Header bar with turn stats, drawn last so it stays on top and legible
    pygame.draw.rect(screen, HEADER_BG, (0, 0, screen.get_width(), HEADER_HEIGHT))
    delivered = sum(1 for d in sim.drones if d.status == DroneStatus.DELIVERED)
    stats = f"Turn {sim.turn}  |  Delivered: {delivered}/{len(sim.drones)}  |  {turn_line}"
    stats_label = font.render(stats, True, pygame.Color("white"))
    screen.blit(stats_label, (10, 9))

    pygame.display.flip()


def run_visual_simulation(g: Graph, K: int, max_turns=200):
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont("monospace", 14, bold=True)
    id_font = pygame.font.SysFont("monospace", 13, bold=True)

    positions = compute_positions(g.network, compute_scale(g.network))
    label_sides = compute_label_sides(g.network)
    max_x = max(p[0] for p in positions.values()) + MARGIN
    max_y = max(p[1] for p in positions.values()) + MARGIN
    screen = pygame.display.set_mode((max_x, max_y))
    pygame.display.set_caption("Fly-In Drone Simulation")

    sim = SimulationState(g)
    drone_paths = assign_paths(g, K)

    turn_line = "(press SPACE to start)"
    draw_frame(screen, font, id_font, g, sim, positions, label_sides, turn_line)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not sim.is_done() and sim.turn <= max_turns:
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
                    moved = sim.execute_moves(legal_moves)
                    for drone_id, _ in legal_moves:
                        drone_paths[drone_id]["progress"] += 1

                    turn_line = sim.format_output(moved) or "(no movement)"
                    sim.turn += 1
                    draw_frame(screen, font, id_font, g, sim, positions, label_sides, turn_line)

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    g = Graph(FlightNetworkParser.parse_file(sys.argv[1]))
    K = g.network.nb_drones
    run_visual_simulation(g, K)