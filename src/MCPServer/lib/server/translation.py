# -*- coding: utf-8 -*-
"""
i18n handling.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import pprint

from django.utils.six import text_type, python_2_unicode_compatible

FALLBACK_LANG = "en"
UNKNOWN_TRANSLATION_LABEL = "<unknown>"


@python_2_unicode_compatible
class TranslationLabel(object):
    """Mixin for easy access to translated messages.

    The JSON-encoded workflow uses ``object`` (mapping type) to associate
    messages for a particular property to language codes, e.g.::

        {
            "en": "cat",
            "es": "gato"
        }

    ``json`` decodes it as a ``dict``. This class wraps the dictionary so it is
    easier to access the translations. Usage example::

        >>> message = {"en": "cat", "es": "gato"}
        >>> tr = TranslationLabel(message)
        >>> tr
        TranslationLabel <{'en': 'cat', 'es': 'gato'}>
        >>> str(tr)
        'cat'
        >>> tr["es"]
        'gato'
        >>> tr["foobar"]
        'cat'
        >>> tr.get_label(lang="es")
        'gato'
        >>> tr.get_label(lang="is", "köttur")
        'köttur'

    """

    def __init__(self, translations):
        if not isinstance(translations, dict):
            translations = {FALLBACK_LANG: text_type(translations)}
        self._src = translations

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, pprint.saferepr(self._src))

    def __str__(self):
        return self.get_label()

    def __getitem__(self, lang):
        return self.get_label(lang)

    def _prepare_lang(self, lang):
        parts = lang.partition("-")
        if parts[1] == "-":
            return "{}_{}".format(parts[0], parts[2].upper())
        return lang

    def get_label(self, lang=FALLBACK_LANG, fallback_label=None):
        """Get the translation of a message.

        It defaults to ``FALLBACK_LANG`` unless ``lang`` is used.
        It accepts a ``fallback_label``,  used when the message is not
        available in the language given. As a last resort, it returns
        ``UNKNOWN_TRANSLATION_LABEL``.
        """
        lang = self._prepare_lang(lang)
        if lang in self._src:
            return self._src[lang]
        if fallback_label is not None:
            return fallback_label
        return self._src.get(FALLBACK_LANG, UNKNOWN_TRANSLATION_LABEL)
