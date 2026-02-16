from pathlib import Path
import sys

for obj in Path(sys.argv[1]).glob(".git/objects/??/*"):
    print(obj)
