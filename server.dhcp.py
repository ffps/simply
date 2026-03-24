#!/usr/bin/python3
import binascii
import logging
import re
import select
import socket
import time
from pprint import pprint

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s", datefmt="%d %b %X")
logger = logging.getLogger()

# simply dhcp server


class DhcpPacket:
    """DHCP Packet"""

    data: bytes
    fields: dict
    opt: dict

    BOOTREQUEST = 1
    BOOTREPLY = 2

    DISCOVER = 1
    OFFER = 2
    REQUEST = 3
    DECLINE = 4
    ACK = 5
    NAK = 6
    RELEASE = 7
    INFORM = 8

    OPT_SUBNET_MASK = 1
    OPT_ROUTER = 3
    OPT_DNS = 6
    OPT_BROADCAST_ADDRESS = 28
    OPT_SERVER_ID = 54
    OPT_LEASE_TIME = 51
    OPT_RENEWAL_TIME = 58
    OPT_REBINDING_TIME = 59
    OPT_OPERATION = 53
    OPT_HOSTNAME = 12
    OPT_VENDOR = 43
    OPT_CLASS_ID = 60
    OPT_CLIENT_ID = 61

    MAGIC = 0x63825363

    OP = {
        DISCOVER: "DISCOVER",
        OFFER: "OFFER",
        REQUEST: "REQUEST",
        DECLINE: "DECLINE",
        ACK: "ACK",
        NAK: "NAK",
        RELEASE: "RELEASE",
        INFORM: "INFORM",
    }

    TYPE = {
        "op": "i8",  # 1:bootrequest, 2:bootreply
        "htype": "i8",  # 1: eth
        "hlen": "i8",
        "hops": "i8",
        "secs": "i16",
        "ciaddr": "ip",
        "yiaddr": "ip",
        "siaddr": "ip",
        "giaddr": "ip",  # 0.0.0.0
        "chaddr": "mac",  # mac 16 bytes
        1: "ip",  # subnet_mask
        3: "ip",  # router
        6: "ip",  # dns
        12: "txt",  # hostname
        28: "ip",  # broadcast_address
        51: "i32",  # lease_time
        54: "ip",  # server_id
        58: "i32",  # renewal_time
        59: "i32",  # rebinding_time
        53: "i8",  # operation
        60: "txt",  # class_id
        61: "mac",  # client_id
        43: "txt",  # client_id
    }

    def __init__(self, data, dump=None):
        self.data = data
        self.fields = self.load_fields(data)
        self.opt = self.load_opts(data)
        if dump:
            self.dump(dump)

    @property
    def payload(self):
        opts = [bytes([opt]) + bytes([len(val)]) + val for opt, val in self.opt.items()]
        return b"".join(self.fields.values()) + b"".join(opts) + b"0xff"

    def load_fields(self, data):
        ret = {
            "op": data[0:1],
            "htype": data[1:2],
            "hlen": data[2:3],
            "hops": data[3:4],
            "xid": data[4:8],
            "secs": data[8:10],
            "flags": data[10:12],
            "ciaddr": data[12:16],
            "yiaddr": data[16:20],
            "siaddr": data[20:24],
            "giaddr": data[24:28],
            "chaddr": data[28:44],
            "sname": data[44:108],
            "file": data[108:236],
            "cookie": data[236:240],
        }
        return ret

    def load_opts(self, data):
        ret = {}
        i = 240
        while i < len(data) and data[i] < 0xFF:
            t = data[i]
            if t:
                l = data[i + 1]
                ret[t] = data[i + 2 : i + 2 + l]
                i = i + 2 + l
            else:
                i += 1
        return ret

    def set_field(self, name, val, obj="fields"):
        i8 = lambda x: chr(x).encode()
        i16 = lambda x: x.to_bytes(2, byteorder="big")
        i32 = lambda x: x.to_bytes(4, byteorder="big")
        ip = socket.inet_aton
        mac = lambda x: binascii.a2b_hex(re.sub(r"[^\da-fA-F]", "", x))
        txt = lambda x: x.encode()

        fn = self.TYPE.get(name, "mac")
        obj = getattr(self, obj)
        obj[name] = locals()[fn](val)
        return obj[name]

    def set_opt(self, name, val):
        return self.set_field(name, val, obj="opt")

    def dump_field(self, name, obj="fields"):
        i8 = ord
        i16 = lambda x: (x[0] << 8) + x[1]
        i32 = lambda x: (x[0] << 24) + (x[1] << 16) + (x[2] << 8) + x[3]
        ip = socket.inet_ntoa
        mac = lambda x: re.sub(r"(..)\B", r"\1:", binascii.b2a_hex(x).decode())
        txt = lambda x: str(x)
        hex = lambda x: "x'" + re.sub(r"(.{12})0+$", r"\1", binascii.b2a_hex(x).decode()) + "'"

        fn = self.TYPE.get(name, "hex")
        return locals()[fn](getattr(self, obj)[name])

    def dump_opt(self, name):
        return self.dump_field(name, obj="opt")

    def dump(self, txt):
        op = ord(self.fields.get("op"))
        logger.info(f"{txt} {self.OP.get(op)}")
        [print(f" {i:7} : {self.dump_field(i)}") for i in self.fields]
        [print(f"  opt.{i:<3}: {self.dump_opt(i)}") for i in self.opt]


class DhcpServer(object):
    """DHCP Server"""

    def __init__(self, config={}, port=67):
        self.config = config
        self.ip = self.config.get("ip") or "0.0.0.0"
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setblocking(0)
        self.sock.bind((self.ip, self.port))
        logger.info(f"DHCP Server started")

    def response(self, op, lease):
        self.packet.set_field("op", DhcpPacket.BOOTREPLY)
        self.packet.set_field("secs", 0)
        self.packet.set_field("flags", "8000")
        self.packet.set_field("yiaddr", lease.get("ip"))
        # self.packet.set_field("ciaddr", "0.0.0.0")

        # options
        self.packet.set_opt(DhcpPacket.OPT_OPERATION, op)
        self.packet.set_opt(DhcpPacket.OPT_SUBNET_MASK, "255.255.255.0")
        self.packet.set_opt(DhcpPacket.OPT_SERVER_ID, self.config.get("router", self.ip))
        self.packet.set_opt(DhcpPacket.OPT_BROADCAST_ADDRESS, re.sub(r"(\d+.\d+.\d+).*", r"\1.255", lease.get("ip")))
        self.packet.set_opt(DhcpPacket.OPT_ROUTER, self.config.get("router", self.ip))
        self.packet.set_opt(DhcpPacket.OPT_DNS, self.config.get("dns", self.ip))
        self.packet.set_opt(DhcpPacket.OPT_LEASE_TIME, 3600)
        self.packet.set_opt(DhcpPacket.OPT_VENDOR, "123456")
        # self.packet.set_opt(DhcpPacket.OPT_RENEWAL_TIME, 3600)
        # self.packet.set_opt(DhcpPacket.OPT_REBINDING_TIME, 3600)

        logger.info(f"OUT({op}) {self.packet.dump_field('yiaddr')}")
        self.sock.sendto(self.packet.payload, ("<broadcast>", 68))
        self.packet.dump(f"OUT")

    def run(self):
        logger.info(f"DHCP Server: started{self.sock.getsockname()}. Press Ctrl+C for stop")
        while True:
            ready, _, _ = select.select([self.sock], [], [], 0.5)
            if ready:
                data = self.sock.recv(0x1000)
                self.packet = DhcpPacket(data, dump="IN")

                mac = self.packet.dump_field("chaddr")[:17]
                op = self.packet.dump_opt(DhcpPacket.OPT_OPERATION)
                logger.info(f"IN ({op}) client:{mac}")
                lease = {"ip": self.config.get("client_ip")}

                if op == DhcpPacket.REQUEST:
                    self.response(DhcpPacket.ACK, lease)

                if op == DhcpPacket.DISCOVER:
                    self.response(DhcpPacket.OFFER, lease)
                    lease["time"] = int(time.time())


if __name__ == "__main__":
    dhcp = DhcpServer(config={"ip": "192.168.0.10", "client_ip": "192.168.0.2"})
    try:
        dhcp.run()
    except KeyboardInterrupt:
        logger.info("Ctrl+C")
