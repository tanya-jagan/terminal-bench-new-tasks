#!/usr/bin/env python3
"""
Verifier for the license-key-reversal task.

Checks that /app/solution.txt contains a valid license key for the
username "tb3testuser", as determined by /app/licensechecker itself.
"""

import subprocess
import sys
import os

SOLUTION_FILE = "/app/solution.txt"
BINARY        = "/app/licensechecker"
USERNAME      = "tb3testuser"


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    # 1. solution file must exist
    if not os.path.isfile(SOLUTION_FILE):
        fail(f"{SOLUTION_FILE} does not exist.")

    # 2. read and clean the key
    with open(SOLUTION_FILE) as f:
        raw = f.read().strip()

    if not raw:
        fail("solution.txt is empty.")

    # Accept keys with or without dashes, normalise to uppercase
    key = raw.upper().replace(" ", "")

    # 3. format check: XXXXX-XXXXX-XXXXX-XXXXX  (23 chars with dashes)
    parts = key.split("-")
    if len(parts) != 4 or any(len(p) != 5 for p in parts):
        fail(
            f"Key '{key}' does not match the required format XXXXX-XXXXX-XXXXX-XXXXX "
            f"(got {len(parts)} groups)."
        )

    BASE36 = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for part in parts:
        for ch in part:
            if ch not in BASE36:
                fail(f"Key contains invalid character '{ch}'.")

    # 4. pass to the binary — this is the authoritative check
    result = subprocess.run(
        [BINARY, USERNAME, key],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and "License valid." in result.stdout:
        print(f"PASS: '{key}' is a valid license key for user '{USERNAME}'.")
        sys.exit(0)
    else:
        fail(
            f"Binary rejected key '{key}' for user '{USERNAME}'.\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}"
        )


if __name__ == "__main__":
    main()