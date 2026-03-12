import cmd

class Echoer(cmd.Cmd):
    """Dumb echo command RePL"""
    prompt = ">> "
    words = "one", "two", "three", "four", "five"

    def do_EOF(self, args):
        return 1

    def do_echo(self, args):
        '''Echo any string'''
        print(args)

    def complete_echo(self, text, line, begidx, endidx):
        return [c for c in self.words if c.startswith(text)]


    def emptyline(self):
        return

if __name__ == "__main__":
    Echoer().cmdloop()
