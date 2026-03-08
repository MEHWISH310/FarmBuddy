import os

class Config:
    BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR  = os.path.join(os.path.dirname(BASE_DIR), 'data')
    MODEL_DIR = os.path.join(os.path.dirname(BASE_DIR), 'models')
    UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), 'uploads')

    os.makedirs(DATA_DIR,  exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'images'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, 'videos'), exist_ok=True)

    MARKET_DATA_PATH = os.path.join(DATA_DIR, 'processed_data', 'market_prices_all_crops.csv')
    FAQ_PATH         = os.path.join(DATA_DIR, 'raw_data', 'faq_dataset.json')
    ADVISORY_PATH    = os.path.join(DATA_DIR, 'raw_data', 'crop_advisory.json')
    SCHEMES_PATH     = os.path.join(DATA_DIR, 'raw_data', 'schemes.json')

    DISEASE_MODEL_PATH = os.path.join(MODEL_DIR, 'disease_model.h5')
    CLASS_INDICES_PATH = os.path.join(MODEL_DIR, 'class_indices.pkl')

    DEBUG = False
    PORT  = 5000
    HOST  = '0.0.0.0'

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'हिन्दी',
        'bn': 'Bengali',
        'te': 'Telugu',
        'ta': 'Tamil',
        'mr': 'Marathi',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'pa': 'Punjabi',
        'or': 'Odia',
        'ur': 'Urdu',
        'ne': 'Nepali',
        'ks': 'Kashmiri',
    }

config = Config()