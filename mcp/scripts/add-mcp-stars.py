#!/usr/bin/env python3
"""Fetch GitHub star counts for repos in mcp-sections/*.md, annotate, and sort.

For each bullet item in `mcp-sections/*.md` whose primary link points to a
GitHub repository (including monorepo subpaths like `/tree/main/...`), fetches
the repository's `stargazerCount` via `gh api graphql` in batches, inserts
`⭐ <count>` immediately after the repo link, and sorts each contiguous list
block by star count descending (non-GitHub or inaccessible repos remain at the
bottom in their original relative order).

Idempotent: re-running refreshes star counts without duplicating badges.

Usage:
    python3 scripts/add-mcp-stars.py [repo-root] [--batch-size 50] [--workers 4] [--dry-run]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BULLET_LINK_RE = re.compile(r"^([-*]\s+\[[^\]]+\]\(([^)]+)\))(.*)$")
EXISTING_STAR_RE = re.compile(r"^\s*⭐\s*[\d,.]+[kKmM]?")
GITHUB_REPO_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)(?:[/?#].*)?$"
)
NON_REPO_OWNERS = frozenset(
    {
        "topics",
        "orgs",
        "users",
        "marketplace",
        "sponsors",
        "features",
        "settings",
        "notifications",
        "explore",
        "trending",
        "collections",
        "events",
        "search",
        "apps",
        "site",
        "about",
        "pricing",
        "enterprise",
        "security",
        "login",
        "join",
        "issues",
        "pulls",
    }
)


def extract_github_repo(url: str) -> Optional[Tuple[str, str]]:
    """Extract (owner, repo) from a GitHub URL, or None if not a GitHub repo."""
    url = url.strip()
    m = GITHUB_REPO_RE.match(url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if owner.lower() in NON_REPO_OWNERS:
        return None
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        return None
    return (owner, repo)


def format_stars(count: int) -> str:
    """Format star count compactly (e.g., 42, 1.2k, 12.5k, 105k, 1.2M)."""
    if count < 1_000:
        return str(count)
    if count < 100_000:
        val = f"{count / 1_000:.1f}"
        if val.endswith(".0"):
            val = val[:-2]
        return f"{val}k"
    if count < 1_000_000:
        return f"{count / 1_000:.0f}k"
    val = f"{count / 1_000_000:.1f}"
    if val.endswith(".0"):
        val = val[:-2]
    return f"{val}M"


def parse_blocks(lines: List[str]) -> List[Tuple[str, object]]:
    """Split lines into ('raw', [lines]) and ('list', [item_lines_list]) blocks.

    Each top-level bullet (`- ` or `* `) is grouped with any immediately
    following indented lines so nested sub-bullets stay attached when sorting.
    """
    blocks: List[Tuple[str, object]] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if BULLET_LINK_RE.match(line):
            items: List[List[str]] = []
            while i < n:
                if BULLET_LINK_RE.match(lines[i]):
                    item = [lines[i]]
                    i += 1
                    while i < n and (
                        lines[i].startswith("  ") or lines[i].startswith("\t")
                    ):
                        item.append(lines[i])
                        i += 1
                    items.append(item)
                else:
                    break
            blocks.append(("list", items))
        else:
            raw: List[str] = []
            while i < n and not BULLET_LINK_RE.match(lines[i]):
                raw.append(lines[i])
                i += 1
            blocks.append(("raw", raw))
    return blocks


def fetch_batch(
    batch: List[Tuple[str, str]],
    retries: int = 3,
) -> Dict[Tuple[str, str], Optional[int]]:
    """Fetch stargazerCount for a batch of (owner, repo) via gh api graphql."""
    fields = []
    for idx, (owner, repo) in enumerate(batch):
        o = json.dumps(owner)
        r = json.dumps(repo)
        fields.append(f"r{idx}: repository(owner: {o}, name: {r}) {{ stargazerCount }}")
    query = "query { " + " ".join(fields) + " }"

    last_err = ""
    for attempt in range(retries):
        proc = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True,
            text=True,
        )
        stdout = proc.stdout.strip()
        if stdout:
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError as e:
                last_err = f"JSON decode error: {e}"
            else:
                data = payload.get("data")
                if isinstance(data, dict):
                    result: Dict[Tuple[str, str], Optional[int]] = {}
                    for idx, (owner, repo) in enumerate(batch):
                        key = (owner.lower(), repo.lower())
                        node = data.get(f"r{idx}")
                        if isinstance(node, dict) and isinstance(
                            node.get("stargazerCount"), int
                        ):
                            result[key] = node["stargazerCount"]
                        else:
                            result[key] = None
                    return result
                last_err = f"No data in GraphQL response: {payload.get('errors') or payload.get('message')}"
        else:
            last_err = proc.stderr.strip() or f"exit code {proc.returncode}"

        time.sleep(1.5 * (attempt + 1))

    # If a whole batch keeps failing and has >1 item, split and retry recursively.
    if len(batch) > 1:
        mid = len(batch) // 2
        left = fetch_batch(batch[:mid], retries=2)
        right = fetch_batch(batch[mid:], retries=2)
        left.update(right)
        return left

    owner, repo = batch[0]
    print(
        f"WARNING: failed to fetch {owner}/{repo}: {last_err}",
        file=sys.stderr,
    )
    return {(owner.lower(), repo.lower()): None}


def fetch_all_stars(
    repos: Dict[Tuple[str, str], Tuple[str, str]],
    batch_size: int = 50,
    workers: int = 4,
) -> Dict[Tuple[str, str], Optional[int]]:
    """Fetch star counts for all unique repos concurrently in GraphQL batches."""
    repo_list = list(repos.values())
    batches = [
        repo_list[i : i + batch_size] for i in range(0, len(repo_list), batch_size)
    ]
    stars: Dict[Tuple[str, str], Optional[int]] = {}
    if not batches:
        return stars

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_batch, b) for b in batches]
        for fut in concurrent.futures.as_completed(futures):
            stars.update(fut.result())
    return stars


def annotate_and_sort_item(
    item: List[str],
    stars: Dict[Tuple[str, str], Optional[int]],
) -> Tuple[int, List[str]]:
    """Annotate a bullet item with its star count and return (sort_stars, lines)."""
    first = item[0]
    m = BULLET_LINK_RE.match(first)
    if not m:
        return (-1, item)

    prefix, url, rest = m.group(1), m.group(2), m.group(3)
    # Strip any previously inserted star tag for idempotency.
    rest_clean = EXISTING_STAR_RE.sub("", rest, count=1)

    gh = extract_github_repo(url)
    if not gh:
        new_first = f"{prefix}{rest_clean}"
        return (-1, [new_first] + item[1:])

    count = stars.get((gh[0].lower(), gh[1].lower()))
    if count is None:
        new_first = f"{prefix}{rest_clean}"
        return (-1, [new_first] + item[1:])

    star_str = f" ⭐ {format_stars(count)}"
    new_first = f"{prefix}{star_str}{rest_clean}"
    return (count, [new_first] + item[1:])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add GitHub star counts and sort entries in mcp-sections/*.md"
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=".",
        help="Path to the repository root (default: current directory)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of repositories per GraphQL query (default: 50)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Concurrent GraphQL workers (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch stars and report stats without modifying files",
    )
    args = parser.parse_args()

    sections_dir = Path(args.repo_root) / "mcp-sections"
    if not sections_dir.is_dir():
        print(f"ERROR: {sections_dir} not found", file=sys.stderr)
        return 1

    md_files = sorted(sections_dir.glob("*.md"))
    parsed_files: Dict[Path, List[Tuple[str, object]]] = {}
    unique_repos: Dict[Tuple[str, str], Tuple[str, str]] = {}
    total_items = 0
    github_items = 0

    for path in md_files:
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        blocks = parse_blocks(lines)
        parsed_files[path] = blocks
        for kind, content in blocks:
            if kind != "list":
                continue
            for item in content:  # type: ignore[union-attr]
                total_items += 1
                m = BULLET_LINK_RE.match(item[0])
                if not m:
                    continue
                gh = extract_github_repo(m.group(2))
                if gh:
                    github_items += 1
                    key = (gh[0].lower(), gh[1].lower())
                    unique_repos.setdefault(key, gh)

    print(
        f"Scanned {len(md_files)} files: {total_items} entries, "
        f"{github_items} GitHub links ({len(unique_repos)} unique repos)"
    )

    t0 = time.time()
    stars = fetch_all_stars(
        unique_repos, batch_size=args.batch_size, workers=args.workers
    )
    elapsed = time.time() - t0

    found_repos = sum(1 for v in stars.values() if v is not None)
    missing_repos = len(stars) - found_repos
    print(
        f"Fetched stars in {elapsed:.1f}s: {found_repos} found, "
        f"{missing_repos} not found/inaccessible"
    )

    files_changed = 0
    for path, blocks in parsed_files.items():
        out_lines: List[str] = []
        for kind, content in blocks:
            if kind == "raw":
                out_lines.extend(content)  # type: ignore[arg-type]
            else:
                annotated = [
                    annotate_and_sort_item(item, stars)
                    for item in content  # type: ignore[union-attr]
                ]
                # Stable sort: highest stars first; -1 (non-GitHub / missing) last.
                annotated.sort(key=lambda pair: pair[0], reverse=True)
                for _, item_lines in annotated:
                    out_lines.extend(item_lines)

        new_text = "\n".join(out_lines)
        old_text = path.read_text(encoding="utf-8")
        if new_text != old_text:
            files_changed += 1
            if not args.dry_run:
                path.write_text(new_text, encoding="utf-8")

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {files_changed}/{len(md_files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
