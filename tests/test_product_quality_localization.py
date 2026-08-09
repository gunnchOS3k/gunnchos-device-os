"""Product-quality tests for localization (CG-QUALITY-007)."""
from __future__ import annotations

from gunnchos_device_os.localization import (
    PRIORITY_LOCALES,
    TOKEN_LOCALIZATION_PASS,
    LocalizationCatalog,
    run_localization,
)


def test_product_quality_localization_pass():
    report = run_localization()
    assert report["ok"] is True
    assert report["token"] == TOKEN_LOCALIZATION_PASS
    assert report["requirement_id"] == "CG-QUALITY-007"
    assert report["full_ui_coverage_claimed"] is False
    assert report["certified_translation_claimed"] is False


def test_product_quality_localization_priority_locales_covered():
    catalog = LocalizationCatalog()
    assert set(catalog.supported_locales()) == set(PRIORITY_LOCALES)
    for loc in PRIORITY_LOCALES:
        result = catalog.coverage(loc)
        assert result.ok is True, loc
        assert result.missing_keys == []


def test_product_quality_localization_negotiates_region_tags():
    catalog = LocalizationCatalog()
    assert catalog.negotiate("es-MX") == "es"
    assert catalog.negotiate("zz-ZZ") == "en"
    text, fallback = catalog.translate("settings.language", "fr")
    assert text == "Langue"
    assert fallback is False
