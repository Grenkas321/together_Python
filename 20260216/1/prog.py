import os, sys, zlib

if len(sys.argv) not in (2, 3):
    print("Usage: prog.py <path-to-repo> [branch]", file=sys.stderr)
    raise SystemExit(1)

repo = sys.argv[1]
git = os.path.join(repo, ".git")
if not os.path.isdir(git):
    print(f"Not a git repository (no .git dir): {repo}", file=sys.stderr)
    raise SystemExit(1)

def read_text(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()

def packed_refs():
    out = {}
    p = os.path.join(git, "packed-refs")
    if not os.path.isfile(p):
        return out
    for line in read_text(p).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("^"):
            continue
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 40:
            out[parts[1]] = parts[0]
    return out

if len(sys.argv) == 2:
    branches = set()
    heads = os.path.join(git, "refs", "heads")
    if os.path.isdir(heads):
        for root, _, files in os.walk(heads):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), heads).replace(os.sep, "/")
                branches.add(rel)
    pref = "refs/heads/"
    for ref, sha in packed_refs().items():
        if ref.startswith(pref):
            branches.add(ref[len(pref):])
    for b in sorted(branches):
        print(b)
    raise SystemExit(0)

branch = sys.argv[2]

sha = None
ref_file = os.path.join(git, "refs", "heads", branch)
if os.path.isfile(ref_file):
    v = read_text(ref_file).strip()
    sha = v if len(v) == 40 else None
else:
    pr = packed_refs()
    sha = pr.get("refs/heads/" + branch)

if not sha:
    print(f"Cannot resolve ref: {branch}", file=sys.stderr)
    raise SystemExit(1)

obj_path = os.path.join(git, "objects", sha[:2], sha[2:])
if not os.path.isfile(obj_path):
    print(f"Object not found: {sha}", file=sys.stderr)
    raise SystemExit(1)

data = zlib.decompress(read_bytes(obj_path))
nul = data.find(b"\x00")
hdr = data[:nul].decode("ascii", errors="replace")
typ = hdr.split()[0] if hdr else ""
body = data[nul + 1:]

if typ != "commit":
    print(f"Expected commit object, got {typ}: {sha}", file=sys.stderr)
    raise SystemExit(1)

text = body.decode("utf-8", errors="replace")
lines = text.splitlines()

i = 0
while i < len(lines):
    line = lines[i]
    i += 1
    if line == "":
        break
    if line.startswith(("tree ", "parent ", "author ", "committer ")):
        print(line)

print()
msg = "\n".join(lines[i:]).rstrip("\n")
if msg:
    print(msg)