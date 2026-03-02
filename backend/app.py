from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
from werkzeug.utils import secure_filename

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Get absolute paths for your project
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)  # FarmBuddy folder
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw_data')
UPLOAD_DIR = os.path.join(PROJECT_ROOT, 'uploads', 'images')

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

from nlp.translator import LanguageTranslator
from data_processor.analyze_prices import PriceAnalyzer
from vision.predict_disease import DiseasePredictor

app = Flask(__name__)
# Updated CORS to include all possible origins
CORS(app, origins=[
    'http://127.0.0.1:5500', 
    'http://localhost:5500', 
    'http://localhost:8000',
    'http://127.0.0.1:5500/frontend',
    'http://localhost:5500/frontend'
])

# Initialize components
translator = LanguageTranslator()
price_analyzer = PriceAnalyzer()
disease_predictor = DiseasePredictor()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/price', methods=['GET'])
def get_price():
    crop = request.args.get('crop')
    state = request.args.get('state')
    market = request.args.get('market')
    
    if not crop:
        return jsonify({"error": "Please provide crop name"}), 400
    
    result = price_analyzer.get_crop_price(crop, state, market)
    return jsonify(result)

@app.route('/api/trend', methods=['GET'])
def get_trend():
    crop = request.args.get('crop')
    state = request.args.get('state')
    days = int(request.args.get('days', 30))
    
    if not crop or not state:
        return jsonify({"error": "Please provide crop and state"}), 400
    
    trend = price_analyzer.get_price_trend(crop, state, days)
    return jsonify(trend)

@app.route('/api/report', methods=['GET'])
def get_report():
    report = price_analyzer.generate_report()
    return jsonify(report)

@app.route('/api/schemes', methods=['GET'])
def get_schemes():
    try:
        # Try multiple possible locations
        possible_paths = [
            os.path.join(RAW_DATA_DIR, 'schemes.json'),
            os.path.join(DATA_DIR, 'schemes.json'),
            os.path.join(DATA_DIR, 'schemes', 'schemes.json'),
            os.path.join(PROJECT_ROOT, 'data', 'schemes.json')
        ]
        
        schemes = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    schemes = json.load(f)
                break
        
        if schemes is None:
            return jsonify({"error": "Schemes file not found", "searched_locations": possible_paths}), 404
            
        return jsonify(schemes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    try:
        # Try multiple possible locations
        possible_paths = [
            os.path.join(RAW_DATA_DIR, 'faq_dataset.json'),
            os.path.join(DATA_DIR, 'faq_dataset.json'),
            os.path.join(DATA_DIR, 'faq', 'faq_dataset.json'),
            os.path.join(PROJECT_ROOT, 'data', 'raw_data', 'faq_dataset.json')
        ]
        
        faqs = None
        faq_path = None
        for path in possible_paths:
            if os.path.exists(path):
                faq_path = path
                with open(path, 'r', encoding='utf-8') as f:
                    faqs = json.load(f)
                break
        
        if faqs is None:
            return jsonify({"error": "FAQ file not found", "searched_locations": possible_paths}), 404
        
        lang = request.args.get('lang', 'en')
        
        if lang == 'en':
            return jsonify(faqs)
        
        translated_faqs = []
        for faq in faqs:
            translated = translator.translate_faq(faq, lang)
            translated_faqs.append(translated)
        
        return jsonify(translated_faqs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faq/search', methods=['GET'])
def search_faqs():
    try:
        query = request.args.get('q', '')
        lang = request.args.get('lang', 'en')
        
        if not query:
            return jsonify({"error": "Please provide search query"}), 400
        
        # Try multiple possible locations
        possible_paths = [
            os.path.join(RAW_DATA_DIR, 'faq_dataset.json'),
            os.path.join(DATA_DIR, 'faq_dataset.json'),
            os.path.join(DATA_DIR, 'faq', 'faq_dataset.json'),
            os.path.join(PROJECT_ROOT, 'data', 'raw_data', 'faq_dataset.json')
        ]
        
        faqs = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    faqs = json.load(f)
                break
        
        if faqs is None:
            return jsonify({"error": "FAQ file not found"}), 404
        
        results = []
        for faq in faqs:
            if (query.lower() in faq['question'].lower() or 
                query.lower() in faq['answer'].lower()):
                if lang == 'en':
                    results.append(faq)
                else:
                    results.append(translator.translate_faq(faq, lang))
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/advisory/<crop>', methods=['GET'])
def get_crop_advisory(crop):
    try:
        # Try multiple possible locations
        possible_paths = [
            os.path.join(RAW_DATA_DIR, 'crop_advisory.json'),
            os.path.join(DATA_DIR, 'crop_advisory.json'),
            os.path.join(DATA_DIR, 'advisory', 'crop_advisory.json'),
            os.path.join(PROJECT_ROOT, 'data', 'raw_data', 'crop_advisory.json')
        ]
        
        advisory = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    advisory = json.load(f)
                break
        
        if advisory is None:
            return jsonify({"error": "Advisory file not found"}), 404
        
        result = [a for a in advisory if a.get('crop', '').lower() == crop.lower()]
        
        if result:
            return jsonify(result[0])
        else:
            return jsonify({"error": f"No advisory found for {crop}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        english_query, original_lang = translator.translate_to_english(query)
        
        intent = 'general'
        if any(word in english_query.lower() for word in ['price', 'rate', 'cost', 'market', 'mandi']):
            intent = 'market_price'
        elif any(word in english_query.lower() for word in ['scheme', 'yojana', 'subsidy', 'sarkari']):
            intent = 'scheme'
        elif any(word in english_query.lower() for word in ['disease', 'spot', 'yellow', 'brown', 'leaf', 'fungus']):
            intent = 'disease'
        
        entities = {}
        crops = ['wheat', 'rice', 'onion', 'potato', 'tomato', 'bajra', 'maize', 'cotton', 'sugarcane']
        for crop in crops:
            if crop in english_query.lower():
                entities['crop'] = crop
                break
        
        if intent == 'market_price' and entities.get('crop'):
            response = f"Checking current market price for {entities['crop']}..."
        elif intent == 'scheme':
            response = "You can check all government schemes at the Schemes section. What specific scheme are you interested in?"
        elif intent == 'disease':
            response = "For disease detection, please upload a photo of your crop using the camera button above."
        else:
            response = "I'm FarmBuddy, your AI farming assistant. I can help you with:\n• Crop prices and market trends\n• Government schemes and subsidies\n• Disease detection from photos\n• Crop advisory and best practices\n\nHow can I assist you today?"
        
        if original_lang != 'en':
            response = translator.translate_text(response, original_lang)
        
        return jsonify({
            'original_query': query,
            'detected_language': original_lang,
            'english_query': english_query,
            'intent': intent,
            'entities': entities,
            'response': response
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict-disease', methods=['POST'])
def predict_disease():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Use jpg, jpeg, png, gif"}), 400
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_DIR, filename)
        file.save(temp_path)
        
        # Check if file was saved successfully
        if not os.path.exists(temp_path):
            return jsonify({"error": "Failed to save image"}), 500
        
        result = disease_predictor.predict(temp_path)
        
        # Clean up - remove the file after processing (optional)
        # os.remove(temp_path)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running"""
    return jsonify({
        "status": "ok", 
        "message": "FarmBuddy API is running",
        "paths": {
            "project_root": PROJECT_ROOT,
            "data_dir": DATA_DIR,
            "raw_data_dir": RAW_DATA_DIR,
            "upload_dir": UPLOAD_DIR
        }
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "FarmBuddy API is running",
        "endpoints": [
            "/api/health",
            "/api/price?crop=onion&state=maharashtra",
            "/api/schemes",
            "/api/faqs?lang=hi",
            "/api/predict-disease (POST)",
            "/api/chat (POST)"
        ]
    })

if __name__ == '__main__':
    print(f"🚀 FarmBuddy Backend Starting...")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"📁 Raw Data Directory: {RAW_DATA_DIR}")
    print(f"📁 Upload Directory: {UPLOAD_DIR}")
    print(f"🌐 Server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)