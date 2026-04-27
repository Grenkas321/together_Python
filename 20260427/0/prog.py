"""The project"""
import sys
from calendar import month

raw_cal = month(int(sys.argv[1]), int(sys.argv[2])).split('\n')
raw_cal[0] = ".. table:: " + raw_cal[0].strip()
raw_cal[-1] = '== == == == == == =='
raw_cal.insert(2, '== == == == == == ==')
raw_cal.insert(1, '== == == == == == ==')
raw_cal.insert(1, '')

for i in range(1, len(raw_cal)):
    raw_cal[i] = '    ' + raw_cal[i]

print('\n'.join(raw_cal))