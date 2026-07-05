import re
import sys
from typing import Dict, Any, List, Optional


class Hub:

    def __init__(self, name: str, x: float, y: float,
                 attributes: Dict[str, Any]):
        self.name: str = name
        self.x: float = x
        self.y: float = y
        self.attributes: Dict[str, Any] = attributes

    @property
    def color(self) -> Optional[str]:
        return self.attributes.get("color")

    @property
    def zone(self) -> Optional[str]:
        return self.attributes.get("zone")

    @property
    def max_drones(self) -> Optional[int]:
        val = self.attributes.get("max_drones")
        return int(val) if val is not None else None

    def __repr__(self) -> str:
        return f"Hub(name='{self.name}', x={self.x}, y={self.y}"
        f", attributes={self.attributes})"


class Connection:

    def __init__(self, hub1: str, hub2: str, attributes: Dict[str, Any]):
        self.hub1: str = hub1
        self.hub2: str = hub2
        self.attributes: Dict[str, Any] = attributes

    @property
    def max_link_capacity(self) -> Optional[int]:
        val = self.attributes.get("max_link_capacity")
        return int(val) if val is not None else None

    def __repr__(self) -> str:
        return f"Connection(hub1='{self.hub1}', hub2='{self.hub2}'"
        f", attributes={self.attributes})"


class FlightNetwork:

    def __init__(self):
        self.nb_drones: int = 0
        self.start_hub: Optional[Hub] = None
        self.end_hub: Optional[Hub] = None
        self.hubs: Dict[str, Hub] = {}
        self.connections: List[Connection] = []

    def add_hub(self, hub: Hub):
        self.hubs[hub.name] = hub

    def add_connection(self, connection: Connection):
        self.connections.append(connection)

    def validate(self) -> List[str]:
        errors = []
        if self.nb_drones <= 0:
            errors.append(f"Invalid nb_drones: must be greater than 0,"
                          f" got {self.nb_drones}")
        if self.start_hub is None:
            errors.append("Start hub is not defined")
        if self.end_hub is None:
            errors.append("End hub is not defined")

        if self.start_hub and self.start_hub.name not in self.hubs:
            errors.append(f"Start hub '{self.start_hub.name}' is defined but "
                          f"missing from the general hubs collection")
        if self.end_hub and self.end_hub.name not in self.hubs:
            errors.append(f"End hub '{self.end_hub.name}' is defined but "
                          f"missing from the general hubs collection")
        for conn in self.connections:
            if conn.hub1 not in self.hubs:
                errors.append(f"Connection refers to unknown hub: "
                              f"'{conn.hub1}'")
            if conn.hub2 not in self.hubs:
                errors.append(f"Connection refers to unknown "
                              f"hub: '{conn.hub2}'")

        return errors

    def __repr__(self) -> str:
        return (
            f"FlightNetwork(\n"
            f"  nb_drones={self.nb_drones},\n"
            f"  start_hub={self.start_hub},\n"
            f"  end_hub={self.end_hub},\n"
            f"  hubs={list(self.hubs.values())},\n"
            f"  connections={self.connections}\n"
            f")"
        )


class FlightNetworkParser:
    @staticmethod
    def _parse_attributes(attr_str: str) -> Dict[str, Any]:
        if not attr_str:
            return {}

        s = attr_str.strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1].strip()

        attrs = {}
        pattern = r'(\w+)=([^\s\\]+)'
        for match in re.finditer(pattern, s):
            key = match.group(1)
            val = match.group(2)

            if val.isdigit():
                attrs[key] = int(val)
            else:
                try:
                    attrs[key] = float(val)
                except ValueError:
                    attrs[key] = val
        return attrs

    @classmethod
    def _parse_hub(cls, val_str: str) -> Hub:
        parts = val_str.split(maxsplit=4)
        if len(parts) < 4:
            raise ValueError(f"Invalid hub format: expected '<name> "
                             f"<x> <y> [attributes]', got '{val_str}'")

        name = parts[0]
        try:
            x = float(parts[1])
            y = float(parts[2])
        except ValueError:
            raise ValueError(f"Coordinates must be numbers, "
                             f"got x='{parts[1]}', y='{parts[2]}'")

        attr_str = parts[3]
        attributes = cls._parse_attributes(attr_str)
        return Hub(name, x, y, attributes)

    @classmethod
    def _parse_connection(cls, val_str: str, known_hubs: List[str])\
            -> Connection:
        parts = val_str.split(maxsplit=1)
        if not parts:
            raise ValueError("Invalid connection format: got empty value")

        endpoints_str = parts[0]
        attr_str = parts[1] if len(parts) > 1 else ""
        attributes = cls._parse_attributes(attr_str)

        endpoints = endpoints_str.split('-')
        if len(endpoints) == 2:
            return Connection(endpoints[0], endpoints[1], attributes)

        for i in range(len(endpoints_str)):
            if endpoints_str[i] == '-':
                h1 = endpoints_str[:i]
                h2 = endpoints_str[i+1:]
                if h1 in known_hubs and h2 in known_hubs:
                    return Connection(h1, h2, attributes)

        if len(endpoints) > 2:
            raise ValueError(f"Ambiguous connection format '{endpoints_str}'."
                             f"Please avoid hyphens in hub names.")
        else:
            raise ValueError(f"Invalid connection format: expected 'hub1-hub2'"
                             f", got '{endpoints_str}'")

    @classmethod
    def parse_string(cls, data: str) -> FlightNetwork:
        network = FlightNetwork()
        lines = data.splitlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' not in line:
                raise ValueError(f"Line {line_num}: Missing colon separator in"
                                 f" line: '{line}'")

            key, val = line.split(':', 1)
            key = key.strip()
            val = val.strip()

            try:
                if key == 'nb_drones':
                    network.nb_drones = int(val)
                elif key == 'start_hub':
                    hub = cls._parse_hub(val)
                    network.start_hub = hub
                    network.add_hub(hub)
                elif key == 'end_hub':
                    hub = cls._parse_hub(val)
                    network.end_hub = hub
                    network.add_hub(hub)
                elif key == 'hub':
                    hub = cls._parse_hub(val)
                    network.add_hub(hub)
                elif key == 'connection':
                    conn = cls._parse_connection(
                        val, list(network.hubs.keys())
                    )
                    network.add_connection(conn)
                else:
                    raise ValueError(f"Unknown key: '{key}'")
            except Exception as e:
                raise ValueError(f"Line {line_num}: "
                                 f"Error parsing '{key}': {e}") from e

        errors = network.validate()
        if errors:
            raise ValueError("Network validation failed:\n"
                             + "\n".join(f"- {err}" for err in errors))

        return network

    @classmethod
    def parse_file(cls, filepath: str) -> FlightNetwork:
        with open(filepath, 'r') as file:
            content = file.read()
        return cls.parse_string(content)


if __name__ == '__main__':

    with open(sys.argv[1], 'r') as file:
        test_input = file.read()

    print("Testing parser with the default example string...")
    try:
        network = FlightNetworkParser.parse_string(test_input)
        print("\nParsing Successful!")
        print(f"Number of drones: {network.nb_drones}")
        print(f"Start Hub: {network.start_hub}")
        print(f"End Hub: {network.end_hub}")
        print(f"Total parsed hubs: {len(network.hubs)}")
        print(f"Total connections: {len(network.connections)}")
        print("\nAll connection details:")
        for idx, conn in enumerate(network.connections, 1):
            print(f"  {idx}. {conn.hub1} <--> {conn.hub2} (capacity: {conn.max_link_capacity}, attrs: {conn.attributes})")
    except Exception as e:
        print(f"Failed to parse test input: {e}", file=sys.stderr)
        sys.exit(1)
