from googletrans import Translator
from langdetect import detect

class LanguageTranslator:
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = {
            'en': 'English',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'te': 'Telugu',
            'ta': 'Tamil',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'or': 'Odia',
            'pa': 'Punjabi',
            'as': 'Assamese',
            'mai': 'Maithili',
            'sat': 'Santali',
            'ks': 'Kashmiri',
            'sd': 'Sindhi',
            'ne': 'Nepali',
            'doi': 'Dogri',
            'mni': 'Manipuri',
            'brx': 'Bodo',
            'ur': 'Urdu',
            'sa': 'Sanskrit'
        }
    
    def detect_language(self, text):
        try:
            lang = detect(text)
            return lang if lang in self.supported_languages else 'en'
        except:
            return 'en'
    
    def translate_to_english(self, text):
        try:
            lang = self.detect_language(text)
            if lang != 'en':
                translated = self.translator.translate(text, dest='en')
                return translated.text, lang
            return text, 'en'
        except:
            return text, 'en'
    
    def translate_text(self, text, target_lang='hi'):
        try:
            if target_lang == 'en':
                return text
            translated = self.translator.translate(text, dest=target_lang)
            return translated.text
        except:
            return text
    
    def translate_faq(self, faq_item, target_lang):
        """Translate a complete FAQ item to target language"""
        translated = {
            'id': faq_item['id'],
            'category': faq_item['category'],
            'tags': faq_item['tags'],
            'original_language': 'en',
            'translated_language': target_lang
        }
        
        # Translate question and answer
        translated['question'] = self.translate_text(faq_item['question'], target_lang)
        translated['answer'] = self.translate_text(faq_item['answer'], target_lang)
        
        return translated