from shlex import join, split

while s := input():
    print(join(split(s)))
