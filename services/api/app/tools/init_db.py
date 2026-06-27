from __future__ import annotations

import argparse

from services.api.app.core import init_db

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize local database schema.")
    parser.add_argument(
        "--seed-test-data",
        action="store_true",
        help="Load v1.1 seed data for test/demo environments only.",
    )
    args = parser.parse_args()
    init_db(seed_test_data=args.seed_test_data)
    suffix = " with test seed data" if args.seed_test_data else ""
    print(f"database initialized{suffix}")
