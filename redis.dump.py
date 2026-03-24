#!/usr/bin/python3
import json

import redis


class RedisDumper:
    redis: redis.Redis
    limit: int = 100

    def __init__(self, host="localhost", port=6379, db=0, **kwargs):
        self.redis = redis.Redis(host=host, port=port, db=db, **kwargs)

    def scan_keys(self, pattern: str = "*", limit: int = None) -> list:
        keys = []
        cursor = 0
        while True:
            cursor, partial_keys = self.redis.scan(cursor=cursor, match=pattern, count=limit or self.limit)
            keys.extend([key.decode() for key in partial_keys])
            if cursor == 0:
                break
        return keys

    def scan_iter(self, pattern: str = "*", limit: int = None):
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor=cursor, match=pattern, count=limit or self.limit)
            for key in keys:
                yield key.decode()
            if cursor == 0:
                break

    def _get_ttl(self, key: str):
        ttl = self.redis.ttl(key)
        return "" if ttl == -1 else ttl

    def dump_json(self, val: str):
        if val.startswith(b"{"):
            try:
                val = json.dumps(json.loads(val.decode()), indent=2)
                return val
            except Exception:
                return val
        return val

    def _get_value(self, key: str, key_type: str):
        try:
            if key_type == "string":
                value = self.redis.get(key)
                return f"'{key}' [{key_type}] {self._get_ttl(key)}: {repr(value)} "

            elif key_type == "hash":
                value = self.redis.hgetall(key)
                return f"'{key}' [{key_type}] {self._get_ttl(key)}: {repr(value)}"

            elif key_type == "list":
                value = self.redis.lrange(key, 0, -1)
                ret = [f"'{key}' [{key_type}({len(value)})] {self._get_ttl(key)}:"]
                for i in range(len(value)):
                    ret.append(f"{i}:{self.dump_json(value[i])}")
                return "\n".join(ret)

            elif key_type == "set":
                value = self.redis.smembers(key)
                ret = [f"'{key}' [{key_type}({len(value)})] {self._get_ttl(key)}:"]
                for i in value:
                    ret.append(f" {self.dump_json(i)}")
                return "\n".join(ret)

            elif key_type == "zset":
                value = self.redis.zrange(key, 0, -1, withscores=True)
                ret = [f"'{key}' [{key_type}({len(value)})] {self._get_ttl(key)}:"]
                for i in value:
                    ret.append(f" {self.dump_json(i)}")
                return "\n".join(ret)
            else:
                return None
        except Exception as e:
            return f"Error: {e}"

    def dump(self, pattern: str = "*", limit: int = None) -> dict:
        for key in self.scan_iter(pattern, limit=limit or self.limit):
            key_type = self.redis.type(key).decode()
            print()
            print(self._get_value(key, key_type))


if __name__ == "__main__":
    rd = RedisDumper()
    rd.dump("*", limit=999)
