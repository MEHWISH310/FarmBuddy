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

# ✅ FIXED: Allow all origins (including null origin from local files)
CORS(app, origins="*", supports_credentials=False)

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
        if any(word in english_query.lower() for word in ['price', 'rate', 'cost', 'market', 'mandi', 'भाव']):
            intent = 'market_price'
        elif any(word in english_query.lower() for word in ['scheme', 'yojana', 'subsidy', 'sarkari', 'योजना']):
            intent = 'scheme'
        elif any(word in english_query.lower() for word in ['disease', 'spot', 'yellow', 'brown', 'leaf', 'fungus', 'रोग']):
            intent = 'disease'
        elif any(word in english_query.lower() for word in ['advisory', 'grow', 'plant', 'fertilizer', 'खाद']):
            intent = 'advisory'
        
        entities = {}
        crops = ['wheat', 'rice', 'onion', 'potato', 'tomato', 'bajra', 'maize', 
                 'cotton', 'sugarcane', 'groundnut', 'soybean', 'mustard', 'बाजरा', 
                 'गेहूं', 'चावल', 'प्याज', 'आलू', 'टमाटर']
        
        for crop in crops:
            if crop.lower() in english_query.lower() or crop.lower() in query.lower():
                entities['crop'] = crop
                break
        
        states = ['punjab', 'haryana', 'uttar pradesh', 'maharashtra', 'karnataka', 
                  'tamil nadu', 'andhra pradesh', 'madhya pradesh', 'rajasthan', 'gujarat',
                  'पंजाब', 'हरियाणा', 'उत्तर प्रदेश', 'महाराष्ट्र']
        
        for state in states:
            if state.lower() in english_query.lower() or state.lower() in query.lower():
                entities['state'] = state
                break
        
        response = ""
        
        if intent == 'market_price':
            if entities.get('crop'):
                state = entities.get('state', 'maharashtra')
                price_result = price_analyzer.get_crop_price(entities['crop'], state)
                
                if 'error' not in price_result:
                    response = f"📊 **{entities['crop'].title()} Market Price**\n\n"
                    response += f"💰 **Modal Price:** ₹{price_result['modal_price']}/quintal\n"
                    response += f"📉 **Min Price:** ₹{price_result['min_price']}/quintal\n"
                    response += f"📈 **Max Price:** ₹{price_result['max_price']}/quintal\n"
                    response += f"📍 **Market:** {price_result['market']}\n"
                    response += f"📅 **Date:** {price_result['date']}\n"
                    if price_result.get('arrival_quantity'):
                        response += f"📦 **Arrival:** {price_result['arrival_quantity']} quintals\n"
                else:
                    response = f"😕 Sorry, I couldn't find price data for {entities['crop']} in {state}. Try another crop or state."
            else:
                response = "Please specify a crop name. For example: 'What is the price of onion in Maharashtra?'"
        
        elif intent == 'scheme':
            try:
                schemes_path = os.path.join(RAW_DATA_DIR, 'schemes.json')
                if os.path.exists(schemes_path):
                    with open(schemes_path, 'r', encoding='utf-8') as f:
                        schemes = json.load(f)
                    if schemes and len(schemes) > 0:
                        response = "📋 **Government Schemes for Farmers:**\n\n"
                        for i, scheme in enumerate(schemes[:3], 1):
                            response += f"{i}. **{scheme.get('name', 'Scheme')}**\n"
                            response += f"   {scheme.get('description', '')[:100]}...\n\n"
                        response += "Type 'more schemes' to see all or visit /api/schemes"
                    else:
                        response = "No schemes found in database."
                else:
                    response = "Scheme information coming soon!"
            except:
                response = "Scheme information coming soon!"
        
        elif intent == 'advisory':
            if entities.get('crop'):
                try:
                    advisory_path = os.path.join(RAW_DATA_DIR, 'crop_advisory.json')
                    if os.path.exists(advisory_path):
                        with open(advisory_path, 'r', encoding='utf-8') as f:
                            advisories = json.load(f)
                        
                        crop_advice = None
                        for adv in advisories:
                            if adv.get('crop', '').lower() == entities['crop'].lower():
                                crop_advice = adv
                                break
                        
                        if crop_advice:
                            response = f"🌱 **{entities['crop'].title()} Growing Guide:**\n\n"
                            if 'season' in crop_advice:
                                response += f"📅 **Season:** {crop_advice['season']}\n"
                            if 'soil' in crop_advice:
                                response += f"🪴 **Soil:** {crop_advice['soil']}\n"
                            if 'varieties' in crop_advice:
                                response += f"🌾 **Varieties:** {crop_advice['varieties']}\n"
                            if 'fertilizer' in crop_advice:
                                response += f"🧪 **Fertilizer:** {crop_advice['fertilizer']}\n"
                        else:
                            response = f"Advisory for {entities['crop']} coming soon!"
                except:
                    response = f"Advisory for {entities['crop']} coming soon!"
            else:
                response = "Please specify a crop name for advisory. For example: 'How to grow tomatoes?'"
        
        elif intent == 'disease':
            response = "🔍 **Disease Detection**\n\nPlease upload a photo of your plant using the camera button above, and I'll identify any diseases and suggest treatments."
        
        else:
            if any(word in english_query.lower() for word in ['hi', 'hello', 'namaste']):
                response = "👋 **Namaste!** I'm FarmBuddy, your AI farming assistant. How can I help you today?\n\n"
                response += "You can ask me about:\n"
                response += "• 🌾 Crop prices (e.g., 'onion price in Maharashtra')\n"
                response += "• 📋 Government schemes\n"
                response += "• 🌱 Farming advice\n"
                response += "• 🔍 Disease detection (upload a photo)"
            else:
                response = "I'm not sure I understood. Try asking about:\n"
                response += "• Market prices: 'What is the price of onion?'\n"
                response += "• Government schemes: 'Show me farmer schemes'\n"
                response += "• Crop advice: 'How to grow tomatoes?'"
        
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
        print(f"Chat error: {e}")
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
        
        if not os.path.exists(temp_path):
            return jsonify({"error": "Failed to save image"}), 500
        
        result = disease_predictor.predict(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
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

@app.route('/api/translate', methods=['POST'])
def translate_text_api():
    try:
        data = request.json
        text = data.get('text', '')
        target_lang = data.get('target_lang', 'en')
        
        if not text or target_lang == 'en':
            return jsonify({'translated_text': text})
        
        translated = translator.translate_text(text, target_lang)
        return jsonify({'translated_text': translated})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 FarmBuddy Backend Starting...")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"📁 Raw Data Directory: {RAW_DATA_DIR}")
    print(f"📁 Upload Directory: {UPLOAD_DIR}")
    print(f"🌐 Server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)