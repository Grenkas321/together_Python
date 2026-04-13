import locale
import gettext
import random


LOCALES = {
    ("ru_RU", "UTF-8"): gettext.translation("wordcount", "po", ["ru_RU.UTF-8"]),
    ("en_US", "UTF-8"): gettext.NullTranslations(),
}

def ngettext(*text):
    return LOCALES[random.choice([("ru_RU", "UTF-8"), ("en_US", "UTF-8")])].ngettext(*text)

while count := input():
    n = len(count.split())
    print(ngettext("Entered {} word", "Entered {} words", n).format(n))