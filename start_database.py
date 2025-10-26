#!/usr/bin/env python
"""Start the FoodTable PostgreSQL database using docker-compose."""
import subprocess
import sys

print("Starting FoodTable PostgreSQL database...")
result = subprocess.run(
    ["docker-compose", "up", "-d", "db"],
    capture_output=False
)

if result.returncode == 0:
    print("\n✓ Database started successfully!")
else:
    print("\n✗ Failed to start database")
    sys.exit(result.returncode)
