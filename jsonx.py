#!/usr/bin/python3
import argparse
import json
import os

import yaml


class CompactJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small containers on single lines."""

    CONTAINER_TYPES = (list, tuple, dict)  # Container datatypes include primitives or other containers
    MAX_WIDTH = 70  # Maximum width of a container that might be put on a single line
    MAX_ITEMS = 2  # Maximum number of items in container that might be put on single line
    INDENT_CHAR = " "

    def __init__(self, level=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indentation_level = 0
        self.level = level or 0  # Maximum levelf for expand

    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            if self._single_line(o):
                return "[" + ", ".join(self.encode(el) for el in o) + "]"
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el) for el in o]
                self.indentation_level -= 1
                return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(o, dict):
            if o:
                if self._single_line(o):
                    return "{" + ", ".join(f"{self.encode(k)}: {self.encode(el)}" for k, el in o.items()) + "}"
                else:
                    self.indentation_level += 1
                    output = [self.indent_str + f"{json.dumps(k)}: {self.encode(v)}" for k, v in o.items()]
                    self.indentation_level -= 1
                    return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
            else:
                return "{}"
        elif isinstance(o, float):
            return f"{o}"
        elif isinstance(o, str):
            o = o.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace('"', '\\"')
            return f'"{o}"'
        else:
            return json.dumps(o)

    def _single_line(self, o):
        return self.indentation_level >= self.level
        # return self._primitives_only(o) and len(o) <= self.MAX_ITEMS and len(str(o)) - 2 <= self.MAX_WIDTH

    def _primitives_only(self, o):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self):
        return self.INDENT_CHAR * (self.indentation_level * self.indent if self.indent else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Format JSON to more readable")
    ap.add_argument("file", help="JSON or YAML file name", type=str, nargs="*")
    ap.add_argument("-l", "--level", help="Max unwrapped nested level , default: 3", type=int, default=3)
    arg = ap.parse_args()

    if arg.file:
        for file in arg.file:
            if os.path.isfile(file):
                out_fname = "{1}.{0}.json".format(arg.level, os.path.splitext(file)[0])
                with open(file, "r", encoding="utf8") as f:
                    if "yaml" in f.name or "yml" in f.name:
                        o = yaml.safe_load(f)
                    else:
                        o = json.load(f)
                print(f" {out_fname}")

                with open(out_fname, "w", encoding="utf8") as f:
                    f.write(json.dumps(o, indent=4, cls=CompactJSONEncoder, level=arg.level))
            else:
                print(f"No file {file}")
    else:
        ap.print_help()
