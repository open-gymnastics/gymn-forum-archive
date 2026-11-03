#!/usr/bin/env python3
"""Check the mirror for completeness.

Writes two reports into reports/:
  links.txt     internal links whose target is missing from site/
                (split into "case mismatch" vs truly missing)
  coverage.txt  how site/ compares with the Wayback seed list:
                - in_wayback_not_local: known URLs we failed to fetch (dead or blocked)
                - not_in_wayback: pages we have that Wayback lacks -> submit these to
                  Save Page Now so they're publicly preserved too

Usage: python3 scripts/verify.py [--site site] [--seeds seeds.txt] [--reports reports]
"""
import argparse
import os
import sys
import urllib.parse
from collections import defaultdict
from html.parser import HTMLParser

HOST = "www.gymn-forum.net"
HOSTS = {HOST, "gymn-forum.net"}
LINK_ATTRS = {"href", "src", "background", "lowsrc", "data"}
HTML_EXT = (".html", ".htm", ".asp", ".shtml")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in LINK_ATTRS and v:
                self.links.append(v.strip())


def read_html(path):
    raw = open(path, "rb").read()
    # FrontPage pages are almost all Windows-1252; fall back gracefully.
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", "replace")


def url_to_rel(url):
    """Turn a gymn-forum URL into a site/-relative path, or None if external."""
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https") or (p.hostname or "") not in HOSTS:
        return None
    path = urllib.parse.unquote(p.path).lstrip("/")
    if path == "" or path.endswith("/"):
        path += "index.html"
    if p.query:
        path += "?" + p.query  # wget keeps the query in the filename
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site")
    ap.add_argument("--seeds", default="seeds.txt")
    ap.add_argument("--reports", default="reports")
    args = ap.parse_args()

    if not os.path.isdir(args.site):
        sys.exit(f"No {args.site}/ directory; run the crawl first.")

    local = set()
    for root, _, files in os.walk(args.site):
        for name in files:
            local.add(os.path.relpath(os.path.join(root, name), args.site).replace(os.sep, "/"))
    lower = defaultdict(list)
    for rel in local:
        lower[rel.lower()].append(rel)

    missing = defaultdict(set)      # target -> pages linking to it
    case_only = defaultdict(set)
    pages = sorted(r for r in local if r.lower().endswith(HTML_EXT))
    for rel in pages:
        base = f"https://{HOST}/" + urllib.parse.quote(rel)
        parser = LinkParser()
        try:
            parser.feed(read_html(os.path.join(args.site, rel)))
        except Exception as e:
            print(f"warn: could not parse {rel}: {e}", file=sys.stderr)
            continue
        for link in parser.links:
            if link.startswith(("mailto:", "javascript:", "#")):
                continue
            target = url_to_rel(urllib.parse.urljoin(base, link.split("#")[0]))
            if not target or target in local:
                continue
            if target.lower() in lower:
                case_only[target].add(rel)
            else:
                missing[target].add(rel)

    os.makedirs(args.reports, exist_ok=True)
    with open(os.path.join(args.reports, "links.txt"), "w", encoding="utf-8") as f:
        f.write(f"Checked {len(pages)} HTML pages.\n\n")
        f.write(f"== Missing targets ({len(missing)}) ==\n")
        for t in sorted(missing):
            f.write(f"{t}\n    linked from: {', '.join(sorted(missing[t])[:5])}\n")
        f.write(f"\n== Case-only mismatches ({len(case_only)}) — file exists with different capitalization ==\n")
        for t in sorted(case_only):
            f.write(f"{t}  ->  {', '.join(lower[t.lower()])}\n")

    summary = [f"{len(pages)} pages checked; {len(missing)} missing link targets; "
               f"{len(case_only)} case-only mismatches"]

    if os.path.exists(args.seeds):
        seeds = {}
        for line in open(args.seeds, encoding="utf-8"):
            rel = url_to_rel(line.strip())
            if rel:
                seeds[rel] = line.strip()
        local_lower = {r.lower() for r in local}
        not_local = sorted(u for r, u in seeds.items() if r.lower() not in local_lower)
        seed_lower = {r.lower() for r in seeds}
        not_wayback = sorted(r for r in pages if r.lower() not in seed_lower)
        with open(os.path.join(args.reports, "coverage.txt"), "w", encoding="utf-8") as f:
            f.write(f"== in_wayback_not_local ({len(not_local)}) — dead on server or crawl failed ==\n")
            f.write("\n".join(not_local) + "\n\n")
            f.write(f"== not_in_wayback ({len(not_wayback)}) — submit these to https://web.archive.org/save ==\n")
            f.write("\n".join(f"https://{HOST}/" + urllib.parse.quote(r) for r in not_wayback) + "\n")
        summary.append(f"{len(not_local)} Wayback URLs not in mirror; {len(not_wayback)} local pages not in Wayback")
    else:
        summary.append("no seeds.txt, skipped Wayback coverage check")

    print("\n".join(summary))
    print(f"Reports written to {args.reports}/")


if __name__ == "__main__":
    main()
