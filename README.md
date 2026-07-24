*This project has been created as part of the 42 curriculum by smoustaj.*

# Fly-In: Autonomous Drone Swarm Routing Simulation

**Fly-In** is a high-performance simulation engine and visualizer written in Python. It models the routing and traversal of an autonomous drone fleet across complex graph networks constrained by hub capacities, connection limits, and distinct zone movement characteristics.

---

## 📖 Description

The goal of **Fly-In** is to guide a fleet of $N$ drones from a designated starting hub (`start_hub`) to a target destination (`end_hub`) in the minimum possible number of simulation turns, without violating any network constraints.

### Key Capabilities & Constraints
* **Zone Movement Types**:
  * `normal`: Standard 1-turn movement between hubs.
  * `priority`: Fast 1-turn movement; prioritized during pathfinding.
  * `restricted`: High-security zone requiring **2 turns** to traverse (1 turn in transit + 1 turn arrival).
  * `blocked`: Entirely inaccessible terrain.
* **Capacity Limits**:
  * **Hub Occupancy (`max_drones`)**: Limits the maximum number of drones concurrently resting in a hub (unrestricted for start/end hubs).
  * **Connection Capacity (`max_link_capacity`)**: Limits the maximum number of drones traversing an edge in a single turn.
* **Conflict & Collision Avoidance**: Prevents node and connection over-saturation through deterministic move validation and arrival reservations.

---

## 🛠️ Instructions

### Prerequisites
* **Python 3.10+**
* **Pygame** (used for visual rendering)

### Installation
Clone the repository and install the required dependencies:

```bash
git clone https://github.com/smoustaj7/fly-in.git
cd fly-in
pip install pygame
```

### Running the Simulation
Execute the simulation engine on any map file:

```bash
python3 -m src maps/easy/01_linear_path.txt
python3 -m src maps/medium/02_circular_loop.txt
python3 -m src maps/hard/01_maze_nightmare.txt
python3 -m src maps/challenger/01_the_impossible_dream.txt
```

### Makefile Targets
The repository includes a `Makefile` for convenient execution, linting, and maintenance:

* `make run` — Runs the simulation on the benchmark *Challenger* map.
* `make lint` — Runs `flake8` and `mypy` strict type checking on the codebase.
* `make clean` — Removes temporary cache directories (`__pycache__`, `.mypy_cache`).

### Running Unit Tests
Execute the unit test suite covering network parser validation and error handling:

```bash
python3 -m unittest discover -s tests
```

---

## 🧠 Algorithm Choices & Implementation Strategy

The core routing and simulation architecture is split into three decoupled modules:

### 1. Flight Network Parsing & Graph Construction ([`src/parsing.py`](file:///home/smoustaj/Desktop/fly-in/src/parsing.py) & [`src/graph.py`](file:///home/smoustaj/Desktop/fly-in/src/graph.py))
* **FlightNetworkParser**: Reads custom flight network configuration files, extracting hubs, coordinates, attributes, and connections while performing strict error validation (checking for invalid capacities, duplicate hub/connection definitions, unrecognized zone types, and missing start/end hubs).
* **Graph Structure**: Builds an adjacency-list representation with zone-weighted traversal costs (cost of 1 for normal/priority zones, cost of 2 for restricted zones).

### 2. Path Assignment & Dynamic Rerouting ([`src/graph.py`](file:///home/smoustaj/Desktop/fly-in/src/graph.py) & [`src/__main__.py`](file:///home/smoustaj/Desktop/fly-in/src/__main__.py))
* **Dijkstra / Shortest Path Computation**: Calculates optimal routes considering zone weights.
* **Fleet Path Distribution (`assign_paths`)**: Distributes optimal and alternative paths across the drone fleet to balance traffic and prevent immediate bottleneck congestion.
* **Dynamic Rerouting on Congestion**: Tracks `stuck_turns` per drone. If a drone remains stuck at a congested hub beyond a threshold (`STUCK_THRESHOLD = 3`), the pathfinding algorithm recalculates an alternate route dynamically by temporarily blocking the congested edge.

### 3. Discrete-Turn Simulation Engine ([`src/engine.py`](file:///home/smoustaj/Desktop/fly-in/src/engine.py))
* **State Machine**: Tracks each drone's status (`WAITING`, `MOVING`, `IN_TRANSIT`, `DELIVERED`).
* **Arrival Reservations (`reserve_arrival`)**: When a drone enters a restricted zone (2-turn traversal), an arrival slot is reserved for `turn + 1`. This guarantees hub capacity is respected when the drone finishes transit.
* **Move Validation (`validate_moves`)**: Validates proposed drone moves per turn against current hub occupancy, departing/entering counts, active connection capacities, and restricted arrival reservations.

---

## 🎨 Visual Representation Features

The interactive visualizer ([`src/visualization.py`](file:///home/smoustaj/Desktop/fly-in/src/visualization.py)) built with Pygame delivers an intuitive real-time graphical representation of the simulation:

* **Interactive Step-Through Control**:
  * Press **`SPACEBAR`** to advance the simulation frame-by-frame, enabling detailed inspection of turn-by-turn drone maneuvers.
* **Dynamic Network Auto-Scaling**:
  * Automatically calculates graph bounding boxes and scales hub positions to fit cleanly on screen regardless of map dimensions.
* **Zone Type Color-Coding**:
  * Hubs are rendered with distinct visual colors matching their zone type (`forestgreen` for normal, `gold` for restricted, `cyan` for priority, `red` for blocked/goal), along with crisp labels displayed above or below nodes.
* **In-Transit Drone Visualization**:
  * Drones moving through 2-turn restricted zones are visually rendered at the midpoint of the connecting edge (`IN_TRANSIT`), giving immediate visual feedback for multi-turn traversals.
* **Multi-Drone Hub Stacking**:
  * Hubs occupied by multiple drones offset drone icons in a grid layout to ensure clear visibility for each drone ID.
* **Real-Time Simulation Dashboard**:
  * A top telemetry header displays the current **Turn Number**, **Delivered Drones Counter** (`X/N`), and formatted move outputs.

---

## 📚 Resources & AI Usage Attribution

### Classic References
* **Dijkstra's Algorithm**: [Dijkstra, E. W. (1959). *A note on two problems in connexion with graphs*](https://doi.org/10.1007/BF01386390).
* **Graph Theory & Pathfinding**: [Red Blob Games: Introduction to A* and Dijkstra](https://www.redblobgames.com/pathfinding/a-star/introduction.html).
* **Pygame Documentation**: [Pygame Front Page & Reference](https://www.pygame.org/docs/).

### AI Usage Attribution
In accordance with the 42 project guidelines, AI assistance was utilized during the development of this project for the following specific tasks:
**Documentation**: Structuring comprehensive technical documentation and README formatting.