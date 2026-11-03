#!/usr/bin/env bash
# Full archive run: Wayback seeds -> crawl -> manifest -> verify.
# Usage: CONTACT=you@example.com ./scripts/run_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/4 Building seed list from the Wayback Machine =="
python3 scripts/wayback_seed.py --out seeds.txt || echo "Seed step failed; crawling from the homepage only."

echo "== 2/4 Crawling =="
./scripts/crawl.sh

echo "== 3/4 Writing manifest =="
python3 scripts/manifest.py

echo "== 4/4 Verifying =="
python3 scripts/verify.py

echo
echo "All done. Review reports/links.txt and reports/coverage.txt, then commit."
