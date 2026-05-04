import locale
import gettext
import random
from . import PATH

locale = locale.setlocale(locale.LC_ALL, locale.getlocale())
translation = gettext.translation("wordcount", PATH, fallback=True)
_, ngettext = translation.gettext, translation.ngettext


while count := input():
    n = len(count.split())
    print(ngettext("Entered {} word", "Entered {} words", n).format(n))
