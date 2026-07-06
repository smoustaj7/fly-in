from .parsing import FlightNetworkParser
import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 -m src <map_file>")
        sys.exit(1)
    network = FlightNetworkParser.parse_file(sys.argv[1])
