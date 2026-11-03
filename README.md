# Gymn Forum Archive

A public preservation backup of **https://www.gymn-forum.net/**, "an electronic forum
for gymnastics since 1995": biographies, digests, articles, and decades of competition
results. The site appears unmaintained, and this copy exists so the material isn't lost
if the domain lapses.

> **Copyright notice.** The original site states that all content is copyrighted
> ("All rights reserved", © Gymn 1995–2022), and most photos are © Debbie Poe. This
> repository is a good-faith preservation copy of an apparently abandoned site, not a
> claim of ownership. All rights remain with the original authors and photographers.
> If you are a rights holder and want content removed or credited differently, open an
> issue or contact the maintainers and it will be handled promptly.

## What's here

| Path | Contents |
|---|---|
| `site/` | Mirror of the site, files byte-for-byte as served (no link rewriting) |
| `warc/` | WARC files from each crawl: the archival-standard capture, headers included (Git LFS) |
| `seeds.txt` | Every URL the Wayback Machine has seen on the domain, used to find orphaned pages |
| `manifest.csv` | One row per file: URL, local path, size, SHA-256 |
| `reports/` | Link-check and coverage reports from `verify.py` |
| `logs/` | Raw crawl logs |
| `scripts/` | Everything needed to re-run the archive |

## Running a crawl

Requirements: `wget` (1.14+ for WARC support), `python3`, `git-lfs`.
On a Mac: `brew install wget git-lfs`.

```bash
git lfs install                      # once per machine
export CONTACT="you@example.com"     # goes in the crawler's user-agent
./scripts/run_all.sh
```

`run_all.sh` does the following:
1. `wayback_seed.py`: pulls the list of known URLs from the Wayback Machine.
2. `crawl.sh`: mirrors the site politely (about 1.5 s between requests, robots.txt
   respected) into `site/` and writes a WARC into `warc/`.
3. `manifest.py`: hashes every file into `manifest.csv`.
4. `verify.py`: checks internal links and Wayback coverage, and writes `reports/`.

Then review the reports and commit:

```bash
git add -A && git commit -m "Crawl $(date +%F)" && git push
```

## Browsing the archive

Pages link to absolute `https://www.gymn-forum.net/...` URLs, so opening `site/`
files directly will send links to the live site. For a faithful offline view, open the
WARC in **[ReplayWeb.page](https://replayweb.page)**. It runs in the browser and is
fully local, so nothing is uploaded.

## Public preservation path

1. Check current coverage: `https://web.archive.org/web/*/gymn-forum.net/*`
2. Submit any URLs listed as `not_in_wayback` in `reports/coverage.txt` to
   Save Page Now (https://web.archive.org/save).
3. Optionally upload the WARC to archive.org as an item. The Internet Archive handles
   rights requests, and they are the appropriate public host.

## Rights and contact log

Record every attempt to reach a rights holder here:

| Date | Who | Method | Result |
|---|---|---|---|
| (years, per maintainer) | gymnforum@gmail.com | Email | No response |
| | Domain WHOIS registrant | | |
| | Debbie Poe (photos) | | |

## Known quirks

- Built with Microsoft FrontPage 4.0. Pages are Windows-1252 encoded, not UTF-8.
- Many paths contain spaces (e.g. `Articles/Gymnast Interviews Profiles/`).
- Paths may differ only by letter case. `verify.py` flags case mismatches separately
  from truly missing files.
