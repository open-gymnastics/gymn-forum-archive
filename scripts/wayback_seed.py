#!/usr/bin/env python3
"""Build seeds.txt from every URL the Wayback Machine has captured on gymn-forum.net.

This finds pages that still exist on the server but are no longer linked from
anywhere, which a normal link-following crawl would miss.

Usage: python3 scripts/wayback_seed.py [--out seeds.txt]
"""
import argparse
import sys
import time
import urllib.parse
import urllib.request

CDX = "https://web.archive.org/cdx/search/cdx"
HOST = "www.gymn-forum.net"
# Skip things that are never real content.
SKIP_SUFFIXES = ("/_vti_bin", "/_vti_cnf", "/_vti_pvt", "/_private", "/cgi-bin")


def fetch(params, attempts=4):
    url = CDX + "?" + urllib.parse.urlencode(params)
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gymn-forum-archive seed builder"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # network hiccups and 429s from the CDX server are common
            wait = 10 * (i + 1)
            print(f"CDX request failed ({e}); retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit("Could not reach the Wayback CDX API.")


def normalize(original):
    """Map any captured variant (http, bare domain, :80, query strings) to one https URL."""
    p = urllib.parse.urlsplit(original.strip())
    if not p.netloc:
        return None
    host = p.hostname or ""
    if host not in ("gymn-forum.net", HOST):
        return None
    path = p.path or "/"
    if any(seg in path for seg in SKIP_SUFFIXES):
        return None
    # Re-quote consistently so "Gymnast Articles INDEX.html" and "%20" forms collapse.
    path = urllib.parse.quote(urllib.parse.unquote(path), safe="/~-_.!*'()")
    query = ("?" + p.query) if p.query else ""
    return f"https://{HOST}{path}{query}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="seeds.txt")
    args = ap.parse_args()

    body = fetch({
        "url": "gymn-forum.net",
        "matchType": "domain",
        "fl": "original",
        "filter": "statuscode:200",
        "collapse": "urlkey",
    })

    urls = sorted({u for u in (normalize(line) for line in body.splitlines()) if u})
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(urls) + "\n")
    print(f"Wrote {len(urls)} unique URLs to {args.out}")


if __name__ == "__main__":
    main()
