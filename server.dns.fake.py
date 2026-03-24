#!/usr/bin/python3
import socket


def dns_domain(data):
    ret = b""
    q_type = (data[2] >> 3) & 15  # Opcode bits
    if q_type == 0:  # Standard query
        ini = 12
        lon = data[ini]
        while lon != 0:
            ret += data[ini + 1 : ini + lon + 1] + b"."
            ini += lon + 1
            lon = data[ini]
    return ret


def dns_response(data, ip):
    ret = (
        data[:2]
        + b"\x81\x80"
        + data[4:6]
        + data[4:6]
        + b"\x00\x00\x00\x00"
        + data[12:]  # Questions and Answers Counts
        + b"\xc0\x0c"  # Original Domain Name Question
        + b"\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"  # Pointer to domain name
        + socket.inet_aton(ip)  # Response type, ttl and resource data length -> 4 bytes  # 4bytes of IP
    )
    return ret


if __name__ == "__main__":
    ip = "192.168.0.10"
    print(f"Fake DNS started on {ip}.\nAll DNS names will be resolved to {ip}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, 53))

    while True:
        data, addr = sock.recvfrom(1024)
        domain = dns_domain(data)
        print([domain])
        if domain:
            sock.sendto(dns_response(data, ip), addr)
            print(f"response: {domain} -> {ip}")
