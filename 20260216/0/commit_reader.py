import sys
import zlib
from pathlib import Path

SHIFT = "  "

repo = Path((sys.argv + ["."])[1]) / ".git"
print(repo)
for obj in repo.glob("objects/??/*"):
    Id = obj.parent.name + obj.name

    header, _, body = zlib.decompress(obj.read_bytes()).partition(b'\x00')
    kind, size = header.split()
    print(Id, kind.decode())
    if kind == b'tree':
        while body:
            treeobj, _, body = body.partition(b'\x00')
            tmode, tname = treeobj.split()
            num, body = body[:20], body[20:]
            print(f"{SHIFT}{tname.decode()} {tmode.decode()} {num.hex()}")
    elif kind == b'commit':
        out = body.decode().replace('\n', '\n' + SHIFT)
        print(f"{SHIFT}{out}")