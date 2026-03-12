import cmd
from calendar import TextCalendar

Month = { 
'JANUARY': 1, 
'FEBRUARY': 2, 
'MARCH': 3, 
'APRIL': 4, 
'MAY': 5, 
'JUNE': 6, 
'JULY': 7, 
'AUGUST': 8, 
'SEPTEMBER': 9, 
'OCTOBER': 10, 
'NOVEMBER': 11, 
'DECEMBER': 12 
}

class CalCMD(cmd.Cmd):
    '''Calendar CmdLine'''

    prompt = ">>> "

    def do_EOF(self, args):
        return True

    def do_prmonth(self, args):
        '''Print a month's calendar as returned by formatmonth()'''
        args = args.split()
        if len(args) == 2:
            TextCalendar().prmonth(int(args[0]), Month[args[1]])
        else:
            print("no args")

    def complete_prmonth(self, text, line, begidx, endidx):
        if len((line[:endidx] + '.').split()) >= 2:
            return [c for c in Month.keys() if c.startswith(text)]

    def do_pryear(self, args):
        '''Print the calendar for an entire year as returned by formatyear()'''
        TextCalendar().pryear(int(args))

if __name__ == "__main__":
    CalCMD().cmdloop()