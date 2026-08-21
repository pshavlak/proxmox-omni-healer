import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import init_db
from backend.importers import import_hysteria_users, import_xui_clients


def main():
    parser = argparse.ArgumentParser(description="Read-only import of existing VPN clients into Mini App DB.")
    parser.add_argument("--hysteria-users", help="Path to Hysteria users.json")
    parser.add_argument("--xui-db", help="Path to x-ui SQLite database")
    parser.add_argument("--default-days", type=int, default=30)
    args = parser.parse_args()

    init_db()
    hysteria_count = import_hysteria_users(args.hysteria_users, args.default_days) if args.hysteria_users else 0
    xui_count = import_xui_clients(args.xui_db, args.default_days) if args.xui_db else 0

    print(f"Imported hysteria={hysteria_count} xui={xui_count}")


if __name__ == "__main__":
    main()
