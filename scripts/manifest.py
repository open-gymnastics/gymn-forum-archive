#!/usr/bin/env python3
"""Write manifest.csv: one row per file in site/ with its URL, size and SHA-256.

The manifest makes later crawls diffable and lets anyone confirm the archive is
intact (re-run and compare hashes).

Usage: python3 scripts/manifest.py [--site site] [--out manifest.csv]
"""
import argparse
import csv
import hashlib
import os
import urllib.parse

HOST = "www.gymn-forum.net"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site")
    ap.add_argument("--out", default="manifest.csv")
    args = ap.parse_args()

    rows = []
    for root, dirs, files in os.walk(args.site):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, args.site).replace(os.sep, "/")
            url = f"https://{HOST}/" + urllib.parse.quote(rel, safe="/~-_.!*'()?=&")
            rows.append((url, rel, os.path.getsize(full), sha256(full)))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "path", "bytes", "sha256"])
        w.writerows(rows)

    total = sum(r[2] for r in rows)
    print(f"Wrote {len(rows)} entries ({total / 1e6:.1f} MB) to {args.out}")


if __name__ == "__main__":
    main()
