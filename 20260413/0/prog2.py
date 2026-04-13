import locale
import gettext
import random

locale = locale.setlocale(locale.LC_ALL, locale.getlocale())
translation = gettext.translation("wordcount", "po", fallback = True)


while count := input():
    n = len(count.split())
    print(translation.gettext("Entered {} word").format(n))