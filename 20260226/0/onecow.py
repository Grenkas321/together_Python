import sys
from cowsay import cowsay, read_dot_cow

if '/' in sys.argv[2]:
    with open(sys.argv[2]) as f:
        the_cow = cowsay.read_dot_cow(f)
    print(cowsay(sys.argv[2], cowfile=the_cow))
else:
    print(cowsay(sys.argv[2], sys.argv[1]))
