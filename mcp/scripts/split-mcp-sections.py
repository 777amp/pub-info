#!/usr/bin/env python3
"""Split MCP.md's Server Implementations sections into per-section files.

Reads MCP.md, extracts every ### section under `## Server Implementations`,
writes each to mcp-sections/<slug>.md, and rewrites MCP.md so its index
links to the section files instead of in-page anchors.

Idempotent: if MCP.md is already split (sections live only in the files),
the section bodies are read back from the existing files and rewritten
unchanged. Running it twice produces no diff.

Usage: python3 split-mcp-sections.py [repo-root]  (default: current directory)
"""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
MCP = ROOT / "MCP.md"
OUT_DIR = ROOT / "mcp-sections"
BACK_LINK = "[← Back to MCP.md](../MCP.md)"

HEADING_RE = re.compile(r'^###\s+(.*?)\s*<a name="([^"]+)"></a>\s*(.+?)\s*$')
INDEX_RE = re.compile(r'^\*\s+(.+?)\s+-\s+\[(.+?)\]\(([^)]+)\)\s*$')


def slugify(name):
    s = name.lower().replace("&", " ")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_heading(line):
    m = HEADING_RE.match(line)
    if not m:
        return None
    return {"emoji": m.group(1).strip(), "anchor": m.group(2),
            "name": m.group(3).strip(), "line": line}


def strip_footer(lines):
    """Remove the back-link footer this script appends to section files."""
    lines = list(lines)
    while lines and lines[-1].strip() == "":
        lines.pop()
    if (len(lines) >= 3 and lines[-1].strip() == BACK_LINK
            and lines[-2].strip() == "" and lines[-3].strip() == "---"):
        lines = lines[:-3]
    while lines and lines[-1].strip() == "":
        lines.pop()
    return lines


def clean_body(lines):
    """Strip the back-link footer and leading/trailing blank lines."""
    lines = strip_footer(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def main():
    text = MCP.read_text(encoding="utf-8")
    lines = text.split("\n")
    si = next(i for i, l in enumerate(lines) if l.startswith("## Server Implementations"))
    fw = next(i for i, l in enumerate(lines) if i > si and l.startswith("## "))
    pre = lines[:si]
    region = lines[si:fw]
    post = lines[fw:]

    note_lines = []
    index_entries = []  # {"emoji", "name", "target"}
    sections = []  # {"emoji", "anchor", "name", "line", "body"}
    cur = None
    for line in region[1:]:  # skip the ## heading itself
        h = parse_heading(line)
        if h:
            if cur is not None:
                sections.append(cur)
            cur = {**h, "body": []}
            continue
        if cur is not None:
            cur["body"].append(line)
            continue
        m = INDEX_RE.match(line)
        if m:
            index_entries.append({"emoji": m.group(1), "name": m.group(2),
                                  "target": m.group(3)})
        elif line.strip():
            note_lines.append(line)
    if cur is not None:
        sections.append(cur)

    index_by_anchor = {e["target"][1:]: e for e in index_entries
                       if e["target"].startswith("#")}
    index_by_slug = {e["target"][len("mcp-sections/"):-3]: e for e in index_entries
                     if e["target"].startswith("mcp-sections/")}

    final = []  # {"slug", "emoji", "name", "heading", "body"}
    if sections:
        for s in sections:
            slug = slugify(s["name"])
            idx = index_by_anchor.get(s["anchor"]) or index_by_slug.get(slug)
            emoji = (idx["emoji"] if idx else s["emoji"]) or s["emoji"]
            name = idx["name"] if idx else s["name"]
            body = clean_body(s["body"])
            meaningful = [l for l in body
                          if l.strip() and l.strip() != BACK_LINK and l.strip() != "---"]
            if not meaningful:
                f = OUT_DIR / f"{slug}.md"
                if f.exists():
                    fl = f.read_text(encoding="utf-8").split("\n")
                    body = clean_body(fl[1:])
                else:
                    print(f"WARNING: no content for '{s['name']}' "
                          f"(no body in MCP.md, no {f}); skipping", file=sys.stderr)
                    continue
            final.append({"slug": slug, "emoji": emoji, "name": name,
                          "heading": s["line"], "body": body})
    else:
        # Already split: rebuild from the index + section files.
        for e in index_entries:
            if not e["target"].startswith("mcp-sections/"):
                print(f"WARNING: index entry '{e['name']}' has no section "
                      f"file; skipping", file=sys.stderr)
                continue
            slug = e["target"][len("mcp-sections/"):-3]
            f = OUT_DIR / f"{slug}.md"
            if not f.exists():
                print(f"WARNING: section file {f} missing; skipping "
                      f"'{e['name']}'", file=sys.stderr)
                continue
            fl = f.read_text(encoding="utf-8").split("\n")
            h = parse_heading(fl[0]) if fl else None
            heading = fl[0] if fl else f"### {e['name']}"
            body = clean_body(fl[1:])
            emoji = e["emoji"] or (h["emoji"] if h else "")
            final.append({"slug": slug, "emoji": emoji, "name": e["name"],
                          "heading": heading, "body": body})

    if not final:
        print("No sections found; nothing to do.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for s in final:
        content = [s["heading"], ""] + s["body"] + ["", "---", "", BACK_LINK, ""]
        (OUT_DIR / f"{s['slug']}.md").write_text("\n".join(content), encoding="utf-8")

    index_lines = [f"* {s['emoji']} - [{s['name']}](mcp-sections/{s['slug']}.md)"
                   for s in final]
    new_region = [lines[si], ""]
    new_region += note_lines
    if note_lines:
        new_region += [""]
    new_region += index_lines
    new_region += [""]
    new_text = "\n".join(pre + new_region + post)
    if not new_text.endswith("\n"):
        new_text += "\n"
    MCP.write_text(new_text, encoding="utf-8")

    print(f"Split {len(final)} sections into {OUT_DIR}/")
    print(f"MCP.md: {len(text.encode('utf-8'))} -> "
          f"{len(new_text.encode('utf-8'))} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
