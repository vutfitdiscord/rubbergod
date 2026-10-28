import sys

from features.health import HealthCheck

if __name__ == "__main__":
    sys.exit(0 if HealthCheck.is_healthy() else 1)
