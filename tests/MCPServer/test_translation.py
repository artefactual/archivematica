from unittest import mock

from server.translation import UNKNOWN_TRANSLATION_LABEL
from server.translation import TranslationLabel


@mock.patch("server.translation.FALLBACK_LANG", "en")
def test_translation_label():
    tr = TranslationLabel({"en": "cat", "es": "gato"})
    assert str(tr) == "cat"
    assert tr["es"] == "gato"
    assert tr["unexistent-lang-code"] == "cat"
    assert tr.get_label(lang="es") == "gato"
    assert tr.get_label(lang="is", fallback_label="köttur") == "köttur"
    assert tr.get_label(lang="??") == "cat"
    with mock.patch("server.translation.FALLBACK_LANG", "xx"):
        assert tr.get_label(lang="yy") == UNKNOWN_TRANSLATION_LABEL


@mock.patch("server.translation.FALLBACK_LANG", "en")
def test_translation_label_with_prepared_codes():
    tr = TranslationLabel({"en": "dog", "pt_BR": "cão"})
    assert tr.get_label(lang="en") == "dog"
    assert tr.get_label(lang="pt-br") == "cão"
    assert tr.get_label(lang="pt_BR") == "cão"
