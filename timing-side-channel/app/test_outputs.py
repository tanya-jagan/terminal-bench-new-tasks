import socket
import sys
import os

CRACKED_FILE = "/app/cracked.txt"

SECRET = os.environ.get("SECRET_PASSWORD", "default_secret_123")

def main():
    if not os.path.exists(CRACKED_FILE):
        print("FAIL")
        sys.exit(1)

    with open(CRACKED_FILE) as f:
        candidate = f.read().strip().splitlines()[0]

    # strict correctness only
    if candidate == SECRET:
        print("PASS")
        sys.exit(0)

    print("FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()