"""
Dummy test client.
Simulates a C2 agent using the raw TCP protocol:
  client -> server : "keepalive <agent_id>"
  server -> client : "OK"  (no task)  or  "<capability>"  (task waiting)

Usage:
    python dummy_client.py [--host 127.0.0.1] [--port 9000] [--interval 5] [--id <10-char-id>]
"""

import argparse
import socket
import sys
import time
import uuid


def _beacon(host: str, port: int, agent_id: str) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        s.connect((host, port))
        s.sendall(f"keepalive {agent_id}".encode())
        s.shutdown(socket.SHUT_WR)
        return s.recv(4096).decode().strip()


def main():
    parser = argparse.ArgumentParser(description="C2 Dummy Test Client")
    parser.add_argument("--host",     default="127.0.0.1", help="Server host")
    parser.add_argument("--port",     type=int, default=9000, help="Server port")
    parser.add_argument("--interval", type=float, default=5.0, help="Beacon interval (seconds)")
    parser.add_argument("--id",       default=None, help="10-char agent ID (random if omitted)")
    args = parser.parse_args()

    agent_id = args.id or uuid.uuid4().hex[:10]
    if len(agent_id) != 10:
        sys.exit("Agent ID must be exactly 10 characters")

    print("=" * 50)
    print("  C2 Dummy Client")
    print("=" * 50)
    print(f"  Agent ID  : {agent_id}")
    print(f"  Server    : {args.host}:{args.port}")
    print(f"  Interval  : {args.interval}s")
    print("=" * 50)
    print()

    while True:
        print(f"[>>] keepalive {agent_id}")

        try:
            response = _beacon(args.host, args.port, agent_id)
            if response == "OK":
                print("[<<] OK (no task)\n")
            else:
                print(f"[<<] command: {response}\n")

        except ConnectionRefusedError:
            print(f"[!!] Cannot reach server at {args.host}:{args.port}\n")
        except Exception as exc:
            print(f"[!!] Unexpected error: {exc}\n")

        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[*] Stopped.")
            break


if __name__ == "__main__":
    main()
