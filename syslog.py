#!/usr/bin/python3
import argparse
import logging
import logging.handlers


def main():
    ap = argparse.ArgumentParser(description="Send test SysLog message")
    ap.add_argument("message", help="Message content", type=str, nargs="?")
    ap.add_argument("-ip", help="Destination IP address. Default: 127.0.0.1", type=str, default="127.0.0.1")
    ap.add_argument("-port", help="Destination port. Default: 514", type=int, default=514)
    arg = ap.parse_args()

    if arg.message:
        syslog_handler = logging.handlers.SysLogHandler(address=(arg.ip, arg.port))
        screen_handler = logging.StreamHandler()
        logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=(screen_handler, syslog_handler))
        logging.info(arg.message)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
