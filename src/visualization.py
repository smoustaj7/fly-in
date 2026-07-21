import sys
import pygame
from src.graph import Graph
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


def compute_scale(network: Graph) -> float:
    xs = [hub.x for hub in network.hubs]
    ys = [hub.y for hub in network.hubs]
    x_range = max(xs) - min(xs) or 1
    y_range = max(ys) - min(ys) or 1
    scale_x = (TARGET_WIDTH - 2 * MARGIN) / x_range
    scale_y = (TARGET_HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / y_range
    return min(scale_x, scale_y, 100)


def get_zone_color(hub_name: str, network: Graph) -> pygame.Color:
    hub = next(h for h in network.hubs if h.name == hub_name)
    if hub.color:
        try:
            return pygame.Color(hub.color)
        except ValueError:
            pass
    return ZONE_TYPE_COLORS.get(hub.zone, pygame.Color("gray"))


def compute_positions(
    network: Graph,
    scale: float
) -> dict[str, tuple[int, int]]:
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


def draw_clouds(screen: pygame.Surface, width: int, height: int) -> None:
    cloud_specs = [
        (0.08, 0.10, 1.0), (0.32, 0.06, 0.8), (0.60, 0.12, 1.1),
        (0.80, 0.05, 0.7), (0.18, 0.20, 0.6), (0.48, 0.18, 0.9),
    ]
    for fx, fy, size in cloud_specs:
        cx, cy = int(width * fx), int(height * fy) + HEADER_HEIGHT + 20
        r = int(18 * size)
        puffs = [
            (0, 0), (r, 4), (-r, 4), (r // 2, -r // 3), (-r // 2, -r // 3)
        ]
        for dx, dy in puffs:
            pygame.draw.circle(
                screen, CLOUD_COLOR, (cx + dx, cy + dy), int(r * 0.9)
            )


def compute_label_sides(network: Graph) -> dict[str, str]:
    sides = {}
    for i, hub in enumerate(network.hubs):
        sides[hub.name] = "above" if i % 2 == 0 else "below"
    return sides


def draw_frame(
    screen: pygame.Surface,
    font: pygame.font.SysFont,
    id_font: pygame.font.SysFont,
    g: Graph,
    sim: SimulationState,
    positions: dict[str, tuple[int, int]],
    label_sides: dict[str, str],
    turn_line: str
) -> None:
    screen.fill(BACKGROUND)
    draw_clouds(screen, screen.get_width(), screen.get_height())

    for zone_name, data in g.graph.items():
        for edge in data["edges"]:
            neighbor = edge[0]
            if neighbor in positions:
                pygame.draw.line(
                    screen, EDGE_COLOR,
                    positions[zone_name], positions[neighbor], 1
                )

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

        bg_rect = pygame.Rect(
            label_x - 3, label_y - 1,
            label.get_width() + 6, label.get_height() + 2
        )
        pygame.draw.rect(screen, LABEL_BG, bg_rect, border_radius=3)
        screen.blit(label, (label_x, label_y))

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
        screen.blit(id_label, (
            drone_pos[0] - id_label.get_width() // 2,
            drone_pos[1] - id_label.get_height() // 2
        ))

    pygame.draw.rect(screen, HEADER_BG, (
        0, 0, screen.get_width(), HEADER_HEIGHT
    ))
    delivered = sum(1 for d in sim.drones if d.status == DroneStatus.DELIVERED)
    stats = f"Turn {sim.turn}  |  Delivered: "
    stats += f"{delivered}/{len(sim.drones)}  |  {turn_line}"
    stats_label = font.render(stats, True, pygame.Color("white"))
    screen.blit(stats_label, (10, 9))

    pygame.display.flip()


class Visualizer:
    def __init__(self, g: Graph):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.SysFont("monospace", 14, bold=True)
        self.id_font = pygame.font.SysFont("monospace", 13, bold=True)
        self.g = g

        self.positions = compute_positions(g.network, compute_scale(g.network))
        self.label_sides = compute_label_sides(g.network)
        max_x = int(max(p[0] for p in self.positions.values()) + MARGIN)
        max_y = int(max(p[1] for p in self.positions.values()) + MARGIN)
        self.screen = pygame.display.set_mode((max_x, max_y))
        pygame.display.set_caption("Fly-In Drone Simulation")

        self.clock = pygame.time.Clock()
        self.waiting = True

    def render(self, sim: SimulationState, turn_line: str):
        draw_frame(
            self.screen, self.font, self.id_font, self.g, sim,
            self.positions, self.label_sides, turn_line or "(no movement)"
        )

        self.waiting = True
        while self.waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN and \
                        event.key == pygame.K_SPACE:
                    self.waiting = False
            self.clock.tick(30)
