from googletrans import Translator
from langdetect import detect

class LanguageTranslator:
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = {
            'as': 'Assamese', 'bn': 'Bengali', 'brx': 'Bodo', 'doi': 'Dogri',
            'en': 'English', 'gu': 'Gujarati', 'hi': 'Hindi', 'kn': 'Kannada',
            'ks': 'Kashmiri', 'kok': 'Konkani', 'mai': 'Maithili', 'ml': 'Malayalam',
            'mni': 'Manipuri', 'mr': 'Marathi', 'ne': 'Nepali', 'or': 'Odia',
            'pa': 'Punjabi', 'sa': 'Sanskrit', 'sat': 'Santali', 'sd': 'Sindhi',
            'ta': 'Tamil', 'te': 'Telugu', 'ur': 'Urdu'
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
        translated = {
            'id': faq_item['id'],
            'category': faq_item['category'],
            'tags': faq_item.get('tags', []),
            'original_language': 'en',
            'translated_language': target_lang
        }
        translated['question'] = self.translate_text(faq_item['question'], target_lang)
        translated['answer'] = self.translate_text(faq_item['answer'], target_lang)
        return translated