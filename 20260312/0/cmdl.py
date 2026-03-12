import cmd
from shlex import split
from pathlib import Path

class SizeCmdl(cmd.Cmd):
    prompt = '>>>'

    def do_size(self, arg):
        """Print size of file"""
        args = split(arg)
        for name in args:
            print(f"{name}: {Path(name).stat().st_size}")
    
    def complete_number(self, text, line, begidx, endidx):
        return [str(p) for p in Path("").glob(f"{text}*")]

    def do_EOF(self, args):
        print("I will be back!")
        return True

if __name__ == "__main__":
    SizeCmdl().cmdloop()
