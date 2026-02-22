import os, sys

if len(sys.argv) != 2:
    print("Usage: prog.py <path-to-repo>", file=sys.stderr)
    raise SystemExit(1)

repo = sys.argv[1]
git = os.path.join(repo, ".git")
if not os.path.isdir(git):
    print(f"Not a git repository (no .git dir): {repo}", file=sys.stderr)
    raise SystemExit(1)

def read_text(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

branches = set()

heads = os.path.join(git, "refs", "heads")
if os.path.isdir(heads):
    for root, _, files in os.walk(heads):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, heads).replace(os.sep, "/")
            branches.add(rel)

packed = os.path.join(git, "packed-refs")
if os.path.isfile(packed):
    for line in read_text(packed).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("^"):
            continue
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 40 and parts[1].startswith("refs/heads/"):
            branches.add(parts[1][len("refs/heads/"):])

for b in sorted(branches):
    print(b)
