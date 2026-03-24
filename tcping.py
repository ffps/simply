#!/usr/bin/python3
import argparse
import re
import socket
import time

RED, GREEN, WHITE, RESET = "\x1b[91m", "\x1b[92m", "\x1b[97m", "\x1b[0m"


def tcping(host, port, timeout=2):
    s = socket.socket()
    s.settimeout(timeout)
    start = time.time()
    try:
        s.connect((host, int(port)))
        s.close()
        ret = round(1000 * (time.time() - start))
        return f"{GREEN}{ret}{RESET} msec"
    except Exception as e:
        return f"{RED}{e}{RESET}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Check connectivity to TCP port")
    ap.add_argument("host", type=str, help="Hostname or IP address", nargs="?")
    ap.add_argument("port", type=int, nargs="?", default=80, help="Destination TCP port number")
    arg = ap.parse_args()

    if arg.host:

        if ":" in arg.host:
            arg.host, arg.port = arg.host.split(":")

        ip = socket.gethostbyname(arg.host)

        print(f"TCP {WHITE}{ip}:{arg.port}{RESET} ... ", end="", flush=True)
        print(tcping(ip, arg.port))
    else:
        ap.print_help()
