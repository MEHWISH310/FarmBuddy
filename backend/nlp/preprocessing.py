import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy

# Download required NLTK data
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')

class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            print("Spacy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def clean_text(self, text):
        """Basic text cleaning"""
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        # Remove extra spaces
        text = ' '.join(text.split())
        return text
    
    def tokenize(self, text):
        """Tokenize text into words"""
        return nltk.word_tokenize(text)
    
    def remove_stopwords(self, tokens):
        """Remove stopwords from tokens"""
        return [token for token in tokens if token not in self.stop_words]
    
    def lemmatize(self, tokens):
        """Lemmatize tokens"""
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def preprocess(self, text):
        """Complete preprocessing pipeline"""
        # Clean text
        cleaned = self.clean_text(text)
        # Tokenize
        tokens = self.tokenize(cleaned)
        # Remove stopwords
        tokens = self.remove_stopwords(tokens)
        # Lemmatize
        tokens = self.lemmatize(tokens)
        return tokens
    
    def preprocess_with_spacy(self, text):
        """Preprocess using spaCy (better NER)"""
        if self.nlp:
            doc = self.nlp(text)
            return [token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha]
        return self.preprocess(text)