from __future__ import annotations

import csv
from pathlib import Path


# Project root: D:\Project\2026\16. AI\Hackathon
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INVENTORY_FILE = PROJECT_ROOT / "data" / "system_inventory.csv"


def get_system_inventory(system_name: str) -> list[dict]:
    """
    Find infrastructure/application components related to a system.

    Example:
        get_system_inventory("Internet Banking")
    """

    results = []

    with INVENTORY_FILE.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            name = row.get("system_name", "")

            if system_name.lower() in name.lower():
                results.append(dict(row))

    return results


if __name__ == "__main__":

    system = "Internet Banking"

    inventory = get_system_inventory(system)

    if not inventory:
        print(f"No system found: {system}")

    else:
        print(f"System found: {system}")
        print()

        for item in inventory:
            for key, value in item.items():
                print(f"{key}: {value}")

            print("-" * 50)