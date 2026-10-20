#!/usr/bin/python3
import argparse
import asyncio
import ipaddress
import logging
import pathlib
import sys

from icmplib import async_ping


class PingScanner:
    logger: logging.Logger
    debug_mode: bool
    scanned: int
    alive: int
    dead: int
    errors: int

    def __init__(self, debug: bool = False) -> None:
        self.debug_mode = debug
        self.logger = self.get_logger()
        self.scanned = 0
        self.alive = 0
        self.dead = 0
        self.errors = 0

    def get_logger(self) -> logging.Logger:
        """Configure console and file logging."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        logger.propagate = False
        logger.handlers.clear()

        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s.%(lineno)s: %(message)s")
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(pathlib.Path(__file__).with_suffix(".log"), encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    async def ping(self, ip: ipaddress.IPv4Address, timeout: int, semaphore: asyncio.Semaphore) -> None:
        """Ping one address without launching an external process."""
        async with semaphore:
            try:
                result = await async_ping(str(ip), count=1, interval=0.2, timeout=timeout, privileged=False)
                if result.is_alive:
                    self.logger.info("%-16s OK %d ms", ip, result.avg_rtt)
                    self.alive += 1
                else:
                    self.logger.debug("%-16s No Response", ip)
                    self.dead += 1
            except Exception as exc:
                self.logger.error("%-16s Ping fail: %s", ip, exc)
                self.errors += 1
            self.scanned += 1

    async def scan(self, net: str, timeout: int, threads: int) -> None:
        """Scan all usable addresses in the supplied CIDR network."""
        try:
            network = ipaddress.ip_network(net, strict=False)
        except ValueError as exc:
            self.logger.error("Invalid network '%s': %s", net, exc)
            return

        if timeout < 1:
            self.logger.error("Timeout must be at least 1 second.")
            return
        if threads < 1:
            self.logger.error("Threads limit must be at least 1.")
            return

        self.logger.info("Start scan net '%s'", network)
        semaphore = asyncio.Semaphore(threads)
        await asyncio.gather(*(self.ping(ip, timeout, semaphore) for ip in network.hosts()))
        self.logger.info("All=%d, OK=%d, dead=%d, errors=%d", self.scanned, self.alive, self.dead, self.errors)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ping scanner")
    ap.add_argument("net", help="Network to scan", type=str, nargs="?", default="192.168.1.0/24")
    ap.add_argument("--timeout", "-t", help="Ping timeout in seconds", type=int, default=2)
    ap.add_argument("--threads", "-n", help="Maximum concurrent pings", type=int, default=100)
    ap.add_argument("--debug", "-d", help="Show non-responsive addresses", action="store_true")
    args = ap.parse_args()

    scanner = PingScanner(debug=args.debug)
    try:
        asyncio.run(scanner.scan(net=args.net, timeout=args.timeout, threads=args.threads))
    except KeyboardInterrupt:
        print("\nScan interrupted.", file=sys.stderr)
