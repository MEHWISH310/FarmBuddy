from googletrans import Translator
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import time

# Fix randomness in langdetect
DetectorFactory.seed = 0

class LanguageTranslator:
    def __init__(self):
        self.translator = Translator()

        # ── Supported languages (removed: brx, doi, kok, mai, mni, sa, sat, sd) ──
        self.supported_languages = {
            'as': 'Assamese',
            'bn': 'Bengali',
            'en': 'English',
            'gu': 'Gujarati',
            'hi': 'Hindi',
            'kn': 'Kannada',
            'ks': 'Kashmiri',
            'ml': 'Malayalam',
            'mr': 'Marathi',
            'ne': 'Nepali',
            'or': 'Odia',
            'pa': 'Punjabi',
            'sd': 'Sindhi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ur': 'Urdu',
        }

        # Languages Google Translate reliably supports
        self.google_supported = {
            'as': 'as',
            'bn': 'bn',
            'gu': 'gu',
            'hi': 'hi',
            'kn': 'kn',
            'ml': 'ml',
            'mr': 'mr',
            'ne': 'ne',
            'or': 'or',
            'pa': 'pa',
            'ta': 'ta',
            'te': 'te',
            'ur': 'ur',
            'en': 'en',
            # Partial support — falls back to Hindi if translation fails
            'ks': 'ur',   # Kashmiri → use Urdu script as closest
            'sd': 'ur',   # Sindhi → Urdu script fallback
        }

        # Languages that fall back to Hindi when Google Translate is unavailable
        self.fallback_to_hindi = {'ks', 'sd'}

    # ── Language Detection ────────────────────────────────────────────────────
    def detect_language(self, text):
        """Detect language of input text. Returns language code."""
        try:
            if not text or len(text.strip()) < 2:
                return 'en'
            lang = detect(text)
            if lang in self.supported_languages:
                return lang
            return 'en'
        except LangDetectException:
            return 'en'
        except Exception:
            return 'en'

    # ── Translate to English ──────────────────────────────────────────────────
    def translate_to_english(self, text):
        """
        Translate any supported language text to English.
        Returns (translated_text, original_language_code).
        """
        try:
            if not text or len(text.strip()) == 0:
                return text, 'en'

            original_lang = self.detect_language(text)

            if original_lang == 'en':
                return text, 'en'

            # Resolve the Google Translate target code
            google_code = self.google_supported.get(original_lang)
            if not google_code:
                return text, original_lang

            time.sleep(0.1)
            translated = self.translator.translate(text, src=google_code, dest='en')
            if translated and translated.text:
                return translated.text, original_lang
            return text, original_lang

        except Exception as e:
            print(f"[Translator] translate_to_english error: {e}")
            return text, 'en'

    # ── Translate to Target Language ──────────────────────────────────────────
    def translate_text(self, text, target_lang='hi'):
        """
        Translate English text to the target language.
        Falls back gracefully for partially supported languages.
        """
        try:
            if not text or len(text.strip()) == 0:
                return text

            if target_lang == 'en':
                return text

            google_code = self.google_supported.get(target_lang)
            if not google_code:
                # Language not supported — return original English text
                return text

            time.sleep(0.1)
            translated = self.translator.translate(text, dest=google_code)
            if translated and translated.text:
                return translated.text
            return text

        except Exception as e:
            print(f"[Translator] translate_text error for '{target_lang}': {e}")
            # Try Hindi fallback for partially supported scripts
            if target_lang in self.fallback_to_hindi:
                try:
                    fallback = self.translator.translate(text, dest='hi')
                    if fallback and fallback.text:
                        return fallback.text
                except Exception:
                    pass
            return text

    # ── Translate Full Response with Markdown Preservation ───────────────────
    def translate_response(self, text, target_lang):
        """
        Translate a response that may contain markdown/emoji.
        Preserves emoji and key formatting where possible.
        """
        if target_lang == 'en' or not text:
            return text

        try:
            # Split on double newlines to translate paragraph by paragraph
            # This preserves structure better than translating the whole blob
            paragraphs = text.split('\n\n')
            translated_parts = []

            for para in paragraphs:
                if para.strip():
                    result = self.translate_text(para.strip(), target_lang)
                    translated_parts.append(result)
                else:
                    translated_parts.append('')

            return '\n\n'.join(translated_parts)

        except Exception as e:
            print(f"[Translator] translate_response error: {e}")
            return self.translate_text(text, target_lang)

    # ── Translate FAQ Item ────────────────────────────────────────────────────
    def translate_faq(self, faq_item, target_lang):
        """Translate an FAQ item dict to the target language."""
        try:
            if target_lang == 'en':
                return faq_item

            translated = {
                'id': faq_item.get('id', 0),
                'category': faq_item.get('category', 'general'),
                'tags': faq_item.get('tags', []),
                'original_language': 'en',
                'translated_language': target_lang,
                'question': self.translate_text(faq_item.get('question', ''), target_lang),
                'answer': self.translate_text(faq_item.get('answer', ''), target_lang),
            }
            return translated

        except Exception as e:
            print(f"[Translator] translate_faq error: {e}")
            return faq_item

    # ── Helpers ───────────────────────────────────────────────────────────────
    def get_language_name(self, lang_code):
        return self.supported_languages.get(lang_code, lang_code)

    def is_supported(self, lang_code):
        return lang_code in self.supported_languages

    def is_google_supported(self, lang_code):
        return lang_code in self.google_supported


# ── Quick self-test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    tr = LanguageTranslator()

    tests = [
        ("प्याज का भाव क्या है?", "Hindi input"),
        ("வெங்காயம் விலை என்ன?", "Tamil input"),
        ("ਕਣਕ ਦਾ ਭਾਅ ਕੀ ਹੈ?", "Punjabi input"),
    ]

    for text, label in tests:
        translated, lang = tr.translate_to_english(text)
        print(f"\n[{label}]")
        print(f"  Original ({lang}): {text}")
        print(f"  English:          {translated}")

    print("\n[EN→TA] Onion price in Tamil Nadu:")
    print(" ", tr.translate_text("Onion price in Tamil Nadu is ₹800 per quintal.", "ta"))