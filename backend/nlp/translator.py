from googletrans import Translator
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import time

# Fix randomness in langdetect
DetectorFactory.seed = 0

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
        
        # Google Translate supports these Indian languages
        self.google_supported = {
            'bn': 'bn', 'gu': 'gu', 'hi': 'hi', 'kn': 'kn', 'ml': 'ml',
            'mr': 'mr', 'pa': 'pa', 'ta': 'ta', 'te': 'te', 'ur': 'ur',
            'en': 'en', 'or': 'or', 'as': 'as', 'ne': 'ne'
        }
    
    def detect_language(self, text):
        """Detect language of input text"""
        try:
            if not text or len(text.strip()) < 2:
                return 'en'
                
            lang = detect(text)
            # Check if detected language is in our supported list
            if lang in self.supported_languages:
                return lang
            else:
                # Default to English for unsupported languages
                return 'en'
        except LangDetectException:
            return 'en'
        except Exception:
            return 'en'
    
    def translate_to_english(self, text):
        """Translate any text to English, return (translated_text, original_language)"""
        try:
            if not text or len(text.strip()) == 0:
                return text, 'en'
                
            original_lang = self.detect_language(text)
            
            # If already English or language not supported by Google Translate
            if original_lang == 'en' or original_lang not in self.google_supported:
                return text, original_lang
            
            # Add small delay to avoid rate limiting
            time.sleep(0.1)
            
            # Translate to English
            translated = self.translator.translate(text, src=original_lang, dest='en')
            
            if translated and translated.text:
                return translated.text, original_lang
            return text, original_lang
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text, 'en'
    
    def translate_text(self, text, target_lang='hi'):
        """Translate text to target language"""
        try:
            if not text or len(text.strip()) == 0:
                return text
                
            # If target is English or not supported, return original
            if target_lang == 'en' or target_lang not in self.google_supported:
                return text
            
            # Add small delay to avoid rate limiting
            time.sleep(0.1)
            
            # Translate to target language
            translated = self.translator.translate(text, dest=target_lang)
            
            if translated and translated.text:
                return translated.text
            return text
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def translate_faq(self, faq_item, target_lang):
        """Translate entire FAQ item to target language"""
        try:
            if target_lang == 'en' or target_lang not in self.google_supported:
                return faq_item
            
            translated = {
                'id': faq_item.get('id', 0),
                'category': faq_item.get('category', 'general'),
                'tags': faq_item.get('tags', []),
                'original_language': 'en',
                'translated_language': target_lang
            }
            
            # Translate question and answer
            if 'question' in faq_item:
                translated['question'] = self.translate_text(faq_item['question'], target_lang)
            else:
                translated['question'] = ''
                
            if 'answer' in faq_item:
                translated['answer'] = self.translate_text(faq_item['answer'], target_lang)
            else:
                translated['answer'] = ''
            
            return translated
            
        except Exception as e:
            print(f"FAQ translation error: {e}")
            return faq_item
    
    def get_language_name(self, lang_code):
        """Get full language name from code"""
        return self.supported_languages.get(lang_code, lang_code)
    
    def is_supported(self, lang_code):
        """Check if language is supported"""
        return lang_code in self.supported_languages

# Test the translator
if __name__ == "__main__":
    translator = LanguageTranslator()
    
    # Test Hindi to English
    hindi_text = "प्याज का भाव क्या है?"
    print(f"Original: {hindi_text}")
    
    translated, lang = translator.translate_to_english(hindi_text)
    print(f"Detected language: {lang}")
    print(f"Translated: {translated}")
    
    # Test English to Hindi
    english_text = "What is the price of onion?"
    hindi = translator.translate_text(english_text, 'hi')
    print(f"\nEnglish: {english_text}")
    print(f"Hindi: {hindi}")