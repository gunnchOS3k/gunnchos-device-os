"""Localization digital scaffold (CG-QUALITY-007).

English-first catalog with priority locales. Provides message lookup and
locale negotiation — not a full translation memory or certified i18n stack.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CLAIM_BOUNDARY = (
    "Digital localization scaffold with English-first catalogs and priority "
    "locale stubs. No certified translation claim; no full UI coverage claim."
)

TOKEN_LOCALIZATION_PASS = "GUNNCHOS_LOCALIZATION_DIGITAL_PASS"

PRIORITY_LOCALES = ("en", "es", "fr", "de", "pt", "ja")

# Minimal product strings — English complete; other locales fall back to en.
_CATALOG: dict[str, dict[str, str]] = {
    "en": {
        "app.name": "gunnchOS",
        "first_run.welcome": "Welcome. Let's set up your device.",
        "destructive.confirm": "Confirm this action to continue.",
        "destructive.cancel": "Cancel",
        "settings.language": "Language",
        "repair.help": "Open repair documentation",
    },
    "es": {
        "app.name": "gunnchOS",
        "first_run.welcome": "Bienvenido. Configuremos tu dispositivo.",
        "destructive.confirm": "Confirma esta acción para continuar.",
        "destructive.cancel": "Cancelar",
        "settings.language": "Idioma",
        "repair.help": "Abrir documentación de reparación",
    },
    "fr": {
        "app.name": "gunnchOS",
        "first_run.welcome": "Bienvenue. Configurons votre appareil.",
        "destructive.confirm": "Confirmez cette action pour continuer.",
        "destructive.cancel": "Annuler",
        "settings.language": "Langue",
        "repair.help": "Ouvrir la documentation de réparation",
    },
    "de": {
        "app.name": "gunnchOS",
        "first_run.welcome": "Willkommen. Richten wir Ihr Gerät ein.",
        "destructive.confirm": "Bestätigen Sie diese Aktion, um fortzufahren.",
        "destructive.cancel": "Abbrechen",
        "settings.language": "Sprache",
        "repair.help": "Reparaturdokumentation öffnen",
    },
    "pt": {
        "app.name": "gunnchOS",
        "first_run.welcome": "Bem-vindo. Vamos configurar seu dispositivo.",
        "destructive.confirm": "Confirme esta ação para continuar.",
        "destructive.cancel": "Cancelar",
        "settings.language": "Idioma",
        "repair.help": "Abrir documentação de reparo",
    },
    "ja": {
        "app.name": "gunnchOS",
        "first_run.welcome": "ようこそ。デバイスをセットアップしましょう。",
        "destructive.confirm": "続行するにはこの操作を確認してください。",
        "destructive.cancel": "キャンセル",
        "settings.language": "言語",
        "repair.help": "修理ドキュメントを開く",
    },
}


@dataclass
class LocalizationResult:
    ok: bool
    locale: str
    resolved_keys: dict[str, str] = field(default_factory=dict)
    missing_keys: list[str] = field(default_factory=list)
    fallback_used: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LocalizationCatalog:
    """Locale negotiation and message lookup over the digital catalog."""

    default_locale: str = "en"
    catalogs: dict[str, dict[str, str]] = field(
        default_factory=lambda: {k: dict(v) for k, v in _CATALOG.items()}
    )

    def supported_locales(self) -> list[str]:
        return list(PRIORITY_LOCALES)

    def negotiate(self, requested: str | None) -> str:
        if not requested:
            return self.default_locale
        req = requested.lower().replace("_", "-")
        primary = req.split("-", 1)[0]
        if primary in self.catalogs:
            return primary
        return self.default_locale

    def translate(self, key: str, locale: str | None = None) -> tuple[str, bool]:
        loc = self.negotiate(locale)
        table = self.catalogs.get(loc) or {}
        if key in table:
            return table[key], False
        en = self.catalogs.get(self.default_locale) or {}
        if key in en:
            return en[key], True
        return key, True

    def coverage(self, locale: str) -> LocalizationResult:
        loc = self.negotiate(locale)
        en_keys = set((self.catalogs.get(self.default_locale) or {}).keys())
        loc_keys = set((self.catalogs.get(loc) or {}).keys())
        missing = sorted(en_keys - loc_keys)
        resolved: dict[str, str] = {}
        fallback_used = False
        for key in sorted(en_keys):
            text, fb = self.translate(key, loc)
            resolved[key] = text
            fallback_used = fallback_used or fb
        ok = loc in PRIORITY_LOCALES and not missing
        return LocalizationResult(
            ok=ok,
            locale=loc,
            resolved_keys=resolved,
            missing_keys=missing,
            fallback_used=fallback_used and loc != self.default_locale,
            details={"claim_boundary": CLAIM_BOUNDARY},
        )


def run_localization() -> dict[str, Any]:
    catalog = LocalizationCatalog()
    reports = {loc: catalog.coverage(loc).to_dict() for loc in PRIORITY_LOCALES}
    ok = all(r["ok"] for r in reports.values()) and catalog.negotiate("es-MX") == "es"
    return {
        "ok": ok,
        "token": TOKEN_LOCALIZATION_PASS if ok else f"{TOKEN_LOCALIZATION_PASS}_FAIL",
        "requirement_id": "CG-QUALITY-007",
        "claim_boundary": CLAIM_BOUNDARY,
        "priority_locales": list(PRIORITY_LOCALES),
        "coverage": reports,
        "full_ui_coverage_claimed": False,
        "certified_translation_claimed": False,
    }
