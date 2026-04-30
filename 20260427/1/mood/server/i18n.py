"""Localization helpers for server-side MOOD messages."""

from pathlib import Path

from babel.support import NullTranslations, Translations

from mood.common.protocol import Payload

DEFAULT_LOCALE = "en_US.UTF8"
TRANSLATION_DOMAIN = "mood_server"
LOCALE_ALIASES = {
    "ru_RU.UTF8": "ru_RU",
    "ru_RU.UTF-8": "ru_RU",
}


class ServerTranslator:
    """Translate server payloads for an individual client locale."""

    def __init__(self, locale_dir: Path | None = None) -> None:
        """Load available translation catalogs from the package directory."""
        catalog_dir = locale_dir or Path(__file__).resolve().parent / "locale"
        self._fallback = NullTranslations()
        self._translations = {
            locale_name: Translations.load(
                dirname=str(catalog_dir),
                locales=[babel_locale],
                domain=TRANSLATION_DOMAIN,
            )
            for locale_name, babel_locale in LOCALE_ALIASES.items()
        }

    def get_translations(self, locale_name: str | None) -> Translations:
        """Return the translation catalog for ``locale_name`` or fallback."""
        if locale_name is None:
            return self._fallback
        return self._translations.get(locale_name, self._fallback)

    def gettext(self, locale_name: str | None, message: str) -> str:
        """Translate a single message for ``locale_name``."""
        return self.get_translations(locale_name).gettext(message)

    def ngettext(
        self,
        locale_name: str | None,
        singular: str,
        plural: str,
        count: int,
    ) -> str:
        """Translate a pluralizable message for ``locale_name``."""
        return self.get_translations(locale_name).ngettext(
            singular,
            plural,
            count,
        )

    def format_hit_points(self, locale_name: str | None, count: int) -> str:
        """Return a localized hit-point phrase for ``count``."""
        template = self.ngettext(
            locale_name,
            "{count} hit point",
            "{count} hit points",
            count,
        )
        return template.format(count=count)

    def localize_payload(
        self,
        locale_name: str | None,
        payload: Payload,
    ) -> Payload:
        """Return a copy of ``payload`` with localized message fields."""
        localized = dict(payload)
        payload_type = str(payload.get("type"))

        if payload_type == "addmon":
            localized["messages"] = self._localize_addmon(locale_name, payload)
        elif payload_type == "attack":
            localized["messages"] = self._localize_attack(locale_name, payload)
        elif payload_type == "monster_move":
            direction = self.gettext(locale_name, str(payload["direction"]))
            localized["message"] = self.gettext(
                locale_name,
                "{name} moved one cell {direction}",
            ).format(
                name=payload["name"],
                direction=direction,
            )
        elif payload_type == "player_joined":
            localized["message"] = self.gettext(
                locale_name,
                "Player {name} joined the game",
            ).format(name=payload["name"])
        elif payload_type == "player_left":
            localized["message"] = self.gettext(
                locale_name,
                "Player {name} left the game",
            ).format(name=payload["name"])
        elif payload_type == "locale":
            localized["message"] = self.gettext(
                locale_name,
                "Set up locale: {locale}",
            ).format(locale=payload["locale"])
        elif payload_type == "movemonsters":
            state = self.gettext(
                locale_name,
                "on" if bool(payload["enabled"]) else "off",
            )
            localized["message"] = self.gettext(
                locale_name,
                "Moving monsters: {state}",
            ).format(state=state)

        return localized

    def _localize_addmon(
        self,
        locale_name: str | None,
        payload: Payload,
    ) -> list[str]:
        """Build localized messages for an ``addmon`` response."""
        hp_text = self.format_hit_points(locale_name, int(payload["hp"]))
        messages = [
            self.gettext(
                locale_name,
                "Added monster {name} to ({x}, {y}) saying {hello} with {hp}",
            ).format(
                name=payload["name"],
                x=payload["x"],
                y=payload["y"],
                hello=payload["hello"],
                hp=hp_text,
            )
        ]
        if bool(payload["replaced"]):
            messages.append(self.gettext(locale_name, "Replaced the old monster"))
        return messages

    def _localize_attack(
        self,
        locale_name: str | None,
        payload: Payload,
    ) -> list[str]:
        """Build localized messages for an ``attack`` response."""
        if payload["result"] == "no_monster":
            if payload["name"] is None:
                return [self.gettext(locale_name, "No monster here")]
            return [
                self.gettext(locale_name, "No {name} here").format(
                    name=payload["name"]
                )
            ]

        damage_text = self.format_hit_points(locale_name, int(payload["damage"]))
        messages = [
            self.gettext(
                locale_name,
                "Attacked {name}, damage {damage}",
            ).format(
                name=payload["name"],
                damage=damage_text,
            )
        ]
        if int(payload["hp"]) == 0:
            messages.append(
                self.gettext(locale_name, "{name} died").format(name=payload["name"])
            )
        else:
            hp_text = self.format_hit_points(locale_name, int(payload["hp"]))
            messages.append(
                self.gettext(
                    locale_name,
                    "{name} now has {hp}",
                ).format(
                    name=payload["name"],
                    hp=hp_text,
                )
            )
        return messages
