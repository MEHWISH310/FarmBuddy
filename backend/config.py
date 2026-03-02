import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
    MODEL_DIR = os.path.join(os.path.dirname(BASE_DIR), 'models')
    UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), 'uploads')
    
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'images'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'videos'), exist_ok=True)
    
    MARKET_DATA_PATH = os.path.join(DATA_DIR, 'processed_data', 'market_prices_all_crops.csv')
    SCHEMES_PATH = os.path.join(DATA_DIR, 'schemes.json')
    FAQ_PATH = os.path.join(DATA_DIR, 'raw_data', 'faq_dataset.json')
    ADVISORY_PATH = os.path.join(DATA_DIR, 'raw_data', 'crop_advisory.json')
    
    DISEASE_MODEL_PATH = os.path.join(MODEL_DIR, 'disease_model.h5')
    CLASS_INDICES_PATH = os.path.join(MODEL_DIR, 'class_indices.pkl')
    
    DEBUG = False
    PORT = 5000
    HOST = '0.0.0.0'
    
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    DEFAULT_LAT = 28.6139
    DEFAULT_LON = 77.2090
    
    SUPPORTED_LANGUAGES = {
        'as': 'Assamese', 'bn': 'Bengali', 'brx': 'Bodo', 'doi': 'Dogri',
        'en': 'English', 'gu': 'Gujarati', 'hi': 'Hindi', 'kn': 'Kannada',
        'ks': 'Kashmiri', 'kok': 'Konkani', 'mai': 'Maithili', 'ml': 'Malayalam',
        'mni': 'Manipuri', 'mr': 'Marathi', 'ne': 'Nepali', 'or': 'Odia',
        'pa': 'Punjabi', 'sa': 'Sanskrit', 'sat': 'Santali', 'sd': 'Sindhi',
        'ta': 'Tamil', 'te': 'Telugu', 'ur': 'Urdu'
    }

config = Config()