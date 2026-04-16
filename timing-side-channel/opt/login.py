import socket
import threading
import time
import random
import os
import collections

# Secret ONLY exists here — injected via start.sh, not a global ENV var.
_SECRET = os.environ.get("SECRET_PASSWORD", "default_secret_123")

# --- timing parameters ---
# Signal: 1ms per correct prefix char.
# Noise:  50ms uniform jitter + occasional 150ms burst.
# To distinguish char N correct vs. incorrect you need ~200+ samples
# (trimmed mean) to beat the noise floor — that's thousands of requests
# per character position for a 12-char secret.
BASE_DELAY  = 0.001   # 1ms signal per correct prefix char
JITTER      = 0.050   # 50ms uniform noise
BURST_PROB  = 0.08    # 8% chance of spike
BURST       = 0.150   # 150ms spike

# --- rate limiting: 5 requests / second per IP ---
RATE_WINDOW = 1.0
RATE_MAX    = 5
_rate_lock  = threading.Lock()
_rate_map   = collections.defaultdict(list)  # ip -> [timestamps]

# --- failure backoff: exponential penalty after repeated wrong guesses ---
BACKOFF_THRESHOLD = 20   # failures before backoff kicks in
BACKOFF_BASE      = 0.5  # seconds, doubles each tier
BACKOFF_MAX       = 30.0
_fail_lock        = threading.Lock()
_fail_map         = collections.defaultdict(int)  # ip -> failure count


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    with _rate_lock:
        _rate_map[ip] = [t for t in _rate_map[ip] if now - t < RATE_WINDOW]
        if len(_rate_map[ip]) >= RATE_MAX:
            return True
        _rate_map[ip].append(now)
        return False


def _backoff_delay(ip: str, success: bool):
    with _fail_lock:
        if success:
            _fail_map[ip] = 0
            return
        _fail_map[ip] += 1
        failures = _fail_map[ip]

    if failures < BACKOFF_THRESHOLD:
        return

    tiers = (failures - BACKOFF_THRESHOLD) // 10
    delay = min(BACKOFF_BASE * (2 ** tiers), BACKOFF_MAX)
    time.sleep(delay)


def _timing_sleep(prefix_len: int):
    t = prefix_len * BASE_DELAY
    t += random.uniform(0, JITTER)
    if random.random() < BURST_PROB:
        t += BURST
    time.sleep(t)


def check(candidate: str) -> bool:
    """Leaks only prefix length via timing — no position output."""
    prefix = 0
    for a, b in zip(candidate, _SECRET):
        if a == b:
            prefix += 1
        else:
            break

    _timing_sleep(prefix)
    return candidate == _SECRET


def handle(conn, addr):
    ip = addr[0]
    try:
        # Rate limit check — instant reject, no timing info leaked.
        if _is_rate_limited(ip):
            conn.sendall(b"RATE_LIMITED\n")
            return

        data = conn.recv(1024).decode().strip()
        if not data:
            return

        result = check(data)

        # Exponential backoff for repeated failures (applied AFTER timing response
        # so it doesn't affect the side-channel measurement meaningfully — it adds
        # to total wall-clock cost of a brute-force campaign).
        _backoff_delay(ip, result)

        conn.sendall(b"OK\n" if result else b"FAIL\n")

    except Exception:
        pass
    finally:
        conn.close()


def serve():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 9876))
    s.listen()

    while True:
        c, addr = s.accept()
        threading.Thread(target=handle, args=(c, addr), daemon=True).start()


if __name__ == "__main__":
    serve()