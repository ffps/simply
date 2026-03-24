#!/usr/bin/python3
# extremely simply sntp server - just for network devices debug purposes

import binascii
import datetime
import logging
import select
import socket
import struct
import sys
import time

try:
    import ntplib
except ImportError:
    print("Required <ntplib>. Please install it with `pip install ntplib`.")
    sys.exit(2)

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s", datefmt="%d %b %X")
logger = logging.getLogger()


def run(ip, port=123):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind((ip, port))
    logger.info(f"NTP Server started on {ip}:{port}. Press Ctrl+C for stop")

    while True:
        ready, _, _ = select.select([sock], [], [], 0.1)
        if ready:
            t = ntplib.system_to_ntp_time(time.time())
            data, addr = sock.recvfrom(0x400)
            packet = ntplib.NTPPacket()
            packet.from_data(data)
            logger.info(f"IN ({addr}) {binascii.b2a_hex(data).decode()}")
            packet.mode = 4
            packet.version = 3
            packet.stratum = 10
            packet.poll = 10
            packet.ref_id = struct.unpack("!I", socket.inet_aton(ip))[0]
            packet.recv_timestamp = t
            packet.ref_timestamp = t
            packet.orig_timestamp = t
            packet.tx_timestamp = t

            sock.sendto(packet.to_data(), addr)
            logger.info(f"OUT({addr}) {binascii.b2a_hex(packet.to_data()).decode()}")


if __name__ == "__main__":
    try:
        ip = sys.argv[1] if len(sys.argv) > 1 else socket.gethostbyname_ex(socket.gethostname())[2][0]
        run(ip)  # use first ip address or type ip in command line
    except KeyboardInterrupt:
        logger.info("Ctrl+C")
