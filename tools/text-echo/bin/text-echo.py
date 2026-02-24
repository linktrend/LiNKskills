#!/usr/bin/env python3
import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Echo text")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("input", nargs="?", default="")
    args = parser.parse_args()

    if args.version:
        print("1.0.0")
        return

    payload = {"status": "ok", "echo": args.input}
    if args.json:
        print(json.dumps(payload))
    else:
        print(args.input)


if __name__ == "__main__":
    main()
