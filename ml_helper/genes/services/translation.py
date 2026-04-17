import logging
from django.conf import settings
from genes.models import Translation
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    return text.strip().lower()


def get_translation_from_db(text: str) -> str | None:
    normalized = normalize_text(text)
    try:
        obj = Translation.objects.get(normalized_text=normalized)
        return obj.translated_text
    except Translation.DoesNotExist:
        return None


def save_translation(text: str, translated: str):
    normalized = normalize_text(text)
    try:
        Translation.objects.get_or_create(
            normalized_text=normalized,
            defaults={
                'source_text': text,
                'translated_text': translated
            }
        )
    except Exception as e:
        logger.debug(f"[Translation] Save error: {e}")


def _translate_via_google(text: str) -> str | None:
    try:
        return GoogleTranslator(source='en', target='ru').translate(text)
    except Exception as e:
        logger.debug(f"[Translation] Google error: {e}")
        return None


def smart_translate_term(term: str) -> str:
    if not term:
        return term

    term = term.strip()

    db_translation = get_translation_from_db(term)
    if db_translation:
        return db_translation

    if getattr(settings, "ENABLE_AUTO_TRANSLATE", True):
        translated = _translate_via_google(term)
        if translated:
            save_translation(term, translated)
            return translated

    logger.info(f"[Translation] Unknown term: '{term}'")
    return term


def translate_list(value) -> str | None:
    if not value:
        return None

    items = value if isinstance(value, list) else [value]

    translated = [
        smart_translate_term(item)
        for item in items if item
    ]

    return ", ".join(translated) if translated else None

def translate_protein_class(value):
    return translate_list(value)


def translate_biological_process(value):
    return translate_list(value)


def translate_molecular_function(value):
    return translate_list(value)