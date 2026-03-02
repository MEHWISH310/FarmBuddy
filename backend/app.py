from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
# Add at top with other imports
from vision.predict_disease import DiseasePredictor
import os
from werkzeug.utils import secure_filename

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your modules
from nlp.translator import LanguageTranslator
from data_processor.analyze_prices import PriceAnalyzer

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize translators and analyzers
translator = LanguageTranslator()
price_analyzer = PriceAnalyzer()

# ============================================
# MARKET PRICE ENDPOINTS
# ============================================

@app.route('/api/price', methods=['GET'])
def get_price():
    """Get price for a crop
    Example: /api/price?crop=onion&state=maharashtra
    """
    crop = request.args.get('crop')
    state = request.args.get('state')
    market = request.args.get('market')
    
    if not crop:
        return jsonify({"error": "Please provide crop name"}), 400
    
    result = price_analyzer.get_crop_price(crop, state, market)
    return jsonify(result)

@app.route('/api/trend', methods=['GET'])
def get_trend():
    """Get price trend
    Example: /api/trend?crop=onion&state=maharashtra&days=7
    """
    crop = request.args.get('crop')
    state = request.args.get('state')
    days = int(request.args.get('days', 30))
    
    if not crop or not state:
        return jsonify({"error": "Please provide crop and state"}), 400
    
    trend = price_analyzer.get_price_trend(crop, state, days)
    return jsonify(trend)

@app.route('/api/report', methods=['GET'])
def get_report():
    """Get market summary report"""
    report = price_analyzer.generate_report()
    return jsonify(report)


# ============================================
# SCHEMES ENDPOINTS
# ============================================

@app.route('/api/schemes', methods=['GET'])
def get_schemes():
    """Get all government schemes"""
    try:
        with open('data/schemes.json', 'r', encoding='utf-8') as f:
            schemes = json.load(f)
        return jsonify(schemes)
    except FileNotFoundError:
        return jsonify({"error": "Schemes file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/schemes/category/<category>', methods=['GET'])
def get_schemes_by_category(category):
    """Get schemes by category (income_support, insurance, credit, etc.)"""
    try:
        with open('data/schemes.json', 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
        
        filtered = [s for s in all_schemes if s.get('category') == category]
        return jsonify(filtered)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# FAQ ENDPOINTS (with translation)
# ============================================

@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    """Get all FAQs in requested language"""
    try:
        with open('data/raw_data/faq_dataset.json', 'r', encoding='utf-8') as f:
            faqs = json.load(f)
        
        # Get language from query parameter (default: en)
        lang = request.args.get('lang', 'en')
        
        if lang == 'en':
            return jsonify(faqs)
        
        # Translate all FAQs
        translated_faqs = []
        for faq in faqs:
            translated = translator.translate_faq(faq, lang)
            translated_faqs.append(translated)
        
        return jsonify(translated_faqs)
    
    except FileNotFoundError:
        return jsonify({"error": "FAQ file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faq/search', methods=['GET'])
def search_faqs():
    """Search FAQs by keyword"""
    try:
        query = request.args.get('q', '')
        lang = request.args.get('lang', 'en')
        
        if not query:
            return jsonify({"error": "Please provide search query"}), 400
        
        with open('data/raw_data/faq_dataset.json', 'r', encoding='utf-8') as f:
            faqs = json.load(f)
        
        # Simple search in English FAQs
        results = []
        for faq in faqs:
            if (query.lower() in faq['question'].lower() or 
                query.lower() in faq['answer'].lower() or
                any(query.lower() in tag for tag in faq.get('tags', []))):
                
                if lang == 'en':
                    results.append(faq)
                else:
                    results.append(translator.translate_faq(faq, lang))
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faq/<int:faq_id>', methods=['GET'])
def get_faq(faq_id):
    """Get single FAQ by ID"""
    try:
        lang = request.args.get('lang', 'en')
        
        with open('data/raw_data/faq_dataset.json', 'r', encoding='utf-8') as f:
            faqs = json.load(f)
        
        for faq in faqs:
            if faq['id'] == faq_id:
                if lang == 'en':
                    return jsonify(faq)
                else:
                    return jsonify(translator.translate_faq(faq, lang))
        
        return jsonify({"error": "FAQ not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# CROP ADVISORY ENDPOINTS
# ============================================

@app.route('/api/advisory', methods=['GET'])
def get_all_advisory():
    """Get all crop advisory"""
    try:
        with open('data/raw_data/crop_advisory.json', 'r', encoding='utf-8') as f:
            advisory = json.load(f)
        return jsonify(advisory)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/advisory/<crop>', methods=['GET'])
def get_crop_advisory(crop):
    """Get advisory for specific crop"""
    try:
        with open('data/raw_data/crop_advisory.json', 'r', encoding='utf-8') as f:
            advisory = json.load(f)
        
        # Filter by crop (case insensitive)
        result = [a for a in advisory if a.get('crop', '').lower() == crop.lower()]
        
        if result:
            return jsonify(result[0])
        else:
            return jsonify({"error": f"No advisory found for {crop}"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# CHAT ENDPOINT (Main NLP)
# ============================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with NLP pipeline"""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Step 1: Detect language and translate to English
        english_query, original_lang = translator.translate_to_english(query)
        
        # Simple intent detection (you can enhance this)
        intent = 'general'
        if any(word in english_query.lower() for word in ['price', 'rate', 'cost']):
            intent = 'market_price'
        elif any(word in english_query.lower() for word in ['scheme', 'yojana', 'subsidy']):
            intent = 'scheme'
        elif any(word in english_query.lower() for word in ['disease', 'spot', 'yellow']):
            intent = 'disease'
        
        # Simple entity extraction
        entities = {}
        crops = ['wheat', 'rice', 'onion', 'potato', 'tomato', 'bajra', 'maize']
        for crop in crops:
            if crop in english_query.lower():
                entities['crop'] = crop
                break
        
        # Generate response based on intent
        if intent == 'market_price' and entities.get('crop'):
            response = f"Checking price for {entities['crop']}..."
        elif intent == 'scheme':
            response = "You can check all government schemes at /api/schemes endpoint"
        else:
            response = "I'm FarmBuddy. Ask me about crop prices, schemes, or upload a photo for disease detection."
        
        # Translate response if needed
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


# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API is running"""
    return jsonify({
        "status": "ok",
        "message": "FarmBuddy API is running",
        "endpoints": [
            "/api/price",
            "/api/trend",
            "/api/report",
            "/api/schemes",
            "/api/faqs",
            "/api/faq/search",
            "/api/advisory",
            "/api/chat",
            "/api/health"
        ]
    })


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    print("="*50)
    print("🌾 FarmBuddy API Server Starting...")
    print("="*50)
    print("\n✅ Endpoints available:")
    print("   - GET  /api/health")
    print("   - GET  /api/price?crop=onion&state=maharashtra")
    print("   - GET  /api/trend?crop=onion&state=maharashtra")
    print("   - GET  /api/report")
    print("   - GET  /api/schemes")
    print("   - GET  /api/faqs?lang=hi")
    print("   - GET  /api/faq/search?q=pm-kisan&lang=te")
    print("   - GET  /api/advisory/wheat")
    print("   - POST /api/chat")
    print("\nServer starting on http://localhost:5000")
    print("="*50)
    
    app.run(debug=True, port=5000)



# Initialize predictor
disease_predictor = DiseasePredictor()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================
# DISEASE DETECTION ENDPOINTS
# ============================================

@app.route('/api/predict-disease', methods=['POST'])
def predict_disease():
    """Predict disease from uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Use jpg, jpeg, png, gif"}), 400
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join('uploads/images', filename)
        file.save(temp_path)
        
        result = disease_predictor.predict(temp_path)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/disease-classes', methods=['GET'])
def get_disease_classes():
    """Get all disease classes"""
    try:
        classes = list(disease_predictor.class_names.values())
        return jsonify({
            'total': len(classes),
            'classes': classes[:10]  # First 10 only
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500