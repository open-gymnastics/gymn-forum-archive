#!/usr/bin/env bash
# Polite full mirror of www.gymn-forum.net into site/, plus a WARC into warc/.
# Usage: CONTACT=you@example.com ./scripts/crawl.sh
set -euo pipefail

cd "$(dirname "$0")/.."

HOST="www.gymn-forum.net"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CONTACT="${CONTACT:?Set CONTACT to an email address for the user-agent}"
UA="gymn-forum-archive/1.0 (private preservation crawl; contact: ${CONTACT})"

mkdir -p site warc logs

# Seed list: the homepage, robots, plus every URL Wayback knows about (if present).
SEEDS="$(mktemp)"
trap 'rm -f "$SEEDS"' EXIT
{
  echo "https://${HOST}/"
  echo "https://${HOST}/robots.txt"
  [[ -f seeds.txt ]] && cat seeds.txt
} | sort -u > "$SEEDS"

echo "Crawling ${HOST} with $(wc -l < "$SEEDS") seed URLs; log: logs/crawl-${STAMP}.log"

# Notes on flags:
#   --mirror                       recursive, infinite depth, timestamping
#   --page-requisites              also fetch images/CSS each page needs
#   --span-hosts + --domains       allow bare gymn-forum.net and www., nothing else
#   --no-host-directories          files land at site/<path>, not site/<host>/<path>
#   --restrict-file-names=nocontrol keep spaces and non-ASCII in names as-is
#   no --convert-links / --adjust-extension: files stay byte-for-byte as served
#   --wait/--random-wait           ~0.75–2.25s between requests; be gentle
# wget exits 8 when some URLs 404, which is normal for Wayback-sourced seeds.
set +e
wget \
  --input-file="$SEEDS" \
  --mirror \
  --page-requisites \
  --span-hosts \
  --domains="${HOST},gymn-forum.net" \
  --no-host-directories \
  --directory-prefix=site \
  --restrict-file-names=nocontrol \
  --wait=1.5 --random-wait \
  --tries=3 --timeout=30 --retry-connrefused \
  --user-agent="$UA" \
  --execute robots=on \
  --warc-file="warc/gymn-forum-${STAMP}" \
  --warc-cdx \
  --warc-max-size=1G \
  --no-verbose \
  --output-file="logs/crawl-${STAMP}.log"
status=$?
set -e

if [[ $status -ne 0 && $status -ne 8 ]]; then
  echo "wget failed with exit code ${status}; see logs/crawl-${STAMP}.log" >&2
  exit "$status"
fi

errors=$(grep -c ' ERROR ' "logs/crawl-${STAMP}.log" || true)
files=$(find site -type f | wc -l | tr -d ' ')
echo "Done. ${files} files in site/, ${errors} fetch errors (mostly expected 404s from old Wayback URLs)."
