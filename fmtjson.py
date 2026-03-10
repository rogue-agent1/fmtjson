#!/usr/bin/env python3
"""fmtjson - JSON formatter, minifier, and validator.

One file. Zero deps. Pretty JSON.

Usage:
  fmtjson.py pretty file.json         → pretty-print
  fmtjson.py mini file.json           → minify
  fmtjson.py validate file.json       → check validity
  fmtjson.py sort file.json           → sort keys
  fmtjson.py flatten file.json        → flatten nested to dot-notation
  fmtjson.py unflatten file.json      → unflatten dot-notation back
  fmtjson.py merge a.json b.json      → deep merge files
  cat file.json | fmtjson.py pretty   → stdin support
"""

import argparse
import json
import sys
from typing import Any


def read_json(path: str | None) -> Any:
    if path and path != "-":
        with open(path) as f:
            return json.load(f)
    return json.loads(sys.stdin.read())


def flatten(obj: Any, prefix: str = "", sep: str = ".") -> dict:
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}{sep}{k}" if prefix else k
            out.update(flatten(v, key, sep))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}[{i}]"
            out.update(flatten(v, key, sep))
    else:
        out[prefix] = obj
    return out


def unflatten(obj: dict, sep: str = ".") -> dict:
    out: dict = {}
    for key, val in obj.items():
        parts = key.replace("[", f"{sep}[").split(sep)
        cur = out
        for i, p in enumerate(parts[:-1]):
            is_arr = p.startswith("[") and p.endswith("]")
            if is_arr:
                p = int(p[1:-1])
            nxt = parts[i + 1]
            nxt_is_arr = nxt.startswith("[") and nxt.endswith("]")
            if isinstance(cur, dict):
                if p not in cur:
                    cur[p] = [] if nxt_is_arr else {}
                cur = cur[p]
            elif isinstance(cur, list):
                while len(cur) <= p:
                    cur.append(None)
                if cur[p] is None:
                    cur[p] = [] if nxt_is_arr else {}
                cur = cur[p]
        last = parts[-1]
        is_arr = last.startswith("[") and last.endswith("]")
        if is_arr:
            idx = int(last[1:-1])
            while len(cur) <= idx:
                cur.append(None)
            cur[idx] = val
        else:
            cur[last] = val
    return out


def deep_merge(a: dict, b: dict) -> dict:
    result = dict(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def cmd_pretty(args):
    data = read_json(args.file)
    indent = args.indent or 2
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def cmd_mini(args):
    data = read_json(args.file)
    print(json.dumps(data, separators=(",", ":"), ensure_ascii=False))


def cmd_validate(args):
    try:
        data = read_json(args.file)
        kind = type(data).__name__
        if isinstance(data, dict):
            print(f"✅ Valid JSON ({kind}, {len(data)} keys)")
        elif isinstance(data, list):
            print(f"✅ Valid JSON ({kind}, {len(data)} items)")
        else:
            print(f"✅ Valid JSON ({kind})")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_sort(args):
    data = read_json(args.file)
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def cmd_flatten_cmd(args):
    data = read_json(args.file)
    print(json.dumps(flatten(data), indent=2, ensure_ascii=False))


def cmd_unflatten_cmd(args):
    data = read_json(args.file)
    print(json.dumps(unflatten(data), indent=2, ensure_ascii=False))


def cmd_merge(args):
    if len(args.files) < 2:
        print("Need at least 2 files to merge", file=sys.stderr)
        return 1
    result = {}
    for f in args.files:
        with open(f) as fh:
            result = deep_merge(result, json.load(fh))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(description="JSON formatter, minifier, and validator")
    p.add_argument("--indent", type=int, default=2)
    sub = p.add_subparsers(dest="cmd")

    for name, fn in [("pretty", cmd_pretty), ("mini", cmd_mini),
                      ("validate", cmd_validate), ("sort", cmd_sort),
                      ("flatten", cmd_flatten_cmd), ("unflatten", cmd_unflatten_cmd)]:
        s = sub.add_parser(name)
        s.add_argument("file", nargs="?")
        s.set_defaults(func=fn)

    s = sub.add_parser("merge")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_merge)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 1
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
