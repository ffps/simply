#!/usr/bin/python3

# Tiny Syslog Server

import logging
import socketserver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s.%(name)s.%(funcName)s.%(lineno)s: %(message)s",
    handlers=(logging.StreamHandler(), logging.FileHandler("syslog.log")),
)

logger = logging.getLogger()


class SyslogHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip())
        logger.info(data)


if __name__ == "__main__":
    try:
        print("Syslog server started. Press Crtl+C to stop")
        server = socketserver.UDPServer(("0.0.0.0", 514), SyslogHandler)
        server.serve_forever(poll_interval=0.1)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Crtl+C Pressed. Exit")
