from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import time
import re
from werkzeug.utils import secure_filename

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw_data')
UPLOAD_DIR = os.path.join(PROJECT_ROOT, 'uploads', 'images')
MARKET_DATA_DIR = os.path.join(DATA_DIR, 'market_data')

os.makedirs(UPLOAD_DIR, exist_ok=True)

from nlp.translator import LanguageTranslator
from data_processor.analyze_prices import PriceAnalyzer
from vision.predict_disease import DiseasePredictor

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False)

translator = LanguageTranslator()
price_analyzer = PriceAnalyzer()
disease_predictor = DiseasePredictor()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Dynamically load available crops from CSV files ─────────────────────────
def get_available_crops():
    crops = []
    search_dirs = [
        MARKET_DATA_DIR,
        os.path.join(DATA_DIR, 'processed_data'),
        RAW_DATA_DIR,
    ]
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith('.csv'):
                    crop_name = os.path.splitext(f)[0].lower().replace('_', ' ').replace('-', ' ')
                    if crop_name.startswith('cleaned ') or crop_name.startswith('market prices'):
                        continue
                    if crop_name not in crops:
                        crops.append(crop_name)
    return crops


# ─── All Indian states ────────────────────────────────────────────────────────
ALL_STATES = [
    'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
    'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
    'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
    'nagaland', 'odisha', 'orissa', 'punjab', 'rajasthan', 'sikkim',
    'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand',
    'west bengal', 'delhi', 'jammu', 'kashmir', 'ladakh',
    'पंजाब', 'हरियाणा', 'उत्तर प्रदेश', 'महाराष्ट्र', 'राजस्थान', 'गुजरात',
    'असम', 'बिहार', 'पश्चिम बंगाल',
]

STATIC_CROPS = [
    'wheat', 'rice', 'onion', 'potato', 'tomato', 'bajra', 'maize', 'corn',
    'cotton', 'sugarcane', 'groundnut', 'soybean', 'mustard', 'barley',
    'sunflower', 'almond', 'arhar', 'arhar dal', 'tur dal', 'chana',
    'jowar', 'ragi', 'millet', 'turmeric', 'ginger', 'garlic', 'chilli',
    'बाजरा', 'गेहूं', 'चावल', 'प्याज', 'आलू', 'टमाटर', 'सरसों', 'मक्का',
]


def detect_crop(text):
    text_lower = text.lower()
    dynamic_crops = get_available_crops()
    all_crops = dynamic_crops + [c for c in STATIC_CROPS if c not in dynamic_crops]
    all_crops_sorted = sorted(all_crops, key=len, reverse=True)
    for crop in all_crops_sorted:
        pattern = r'\b' + re.escape(crop) + r'\b'
        if re.search(pattern, text_lower):
            return crop
    return None


def detect_state(text):
    text_lower = text.lower()
    for state in sorted(ALL_STATES, key=len, reverse=True):
        pattern = r'\b' + re.escape(state) + r'\b'
        if re.search(pattern, text_lower):
            return state
    return None


# ─── Helper: translate response if needed ────────────────────────────────────
def maybe_translate(text, target_lang):
    """Translate text to target_lang if it's not English."""
    if not target_lang or target_lang == 'en':
        return text
    return translator.translate_response(text, target_lang)


# ─── Routes ───────────────────────────────────────────────────────────────────
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
    return jsonify(price_analyzer.generate_report())

@app.route('/api/schemes', methods=['GET'])
def get_schemes():
    try:
        for path in [
            os.path.join(RAW_DATA_DIR, 'schemes.json'),
            os.path.join(DATA_DIR, 'schemes.json'),
        ]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))
        return jsonify({"error": "Schemes file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    try:
        for path in [
            os.path.join(RAW_DATA_DIR, 'faq_dataset.json'),
            os.path.join(DATA_DIR, 'faq_dataset.json'),
        ]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    faqs = json.load(f)
                lang = request.args.get('lang', 'en')
                if lang == 'en':
                    return jsonify(faqs)
                return jsonify([translator.translate_faq(faq, lang) for faq in faqs])
        return jsonify({"error": "FAQ file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/faq/search', methods=['GET'])
def search_faqs():
    try:
        query = request.args.get('q', '')
        lang = request.args.get('lang', 'en')
        if not query:
            return jsonify({"error": "Please provide search query"}), 400
        for path in [os.path.join(RAW_DATA_DIR, 'faq_dataset.json'), os.path.join(DATA_DIR, 'faq_dataset.json')]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    faqs = json.load(f)
                results = [faq for faq in faqs if query.lower() in faq['question'].lower() or query.lower() in faq['answer'].lower()]
                if lang != 'en':
                    results = [translator.translate_faq(r, lang) for r in results]
                return jsonify(results)
        return jsonify({"error": "FAQ file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/advisory/<crop>', methods=['GET'])
def get_crop_advisory(crop):
    try:
        lang = request.args.get('lang', 'en')
        for path in [os.path.join(RAW_DATA_DIR, 'crop_advisory.json'), os.path.join(DATA_DIR, 'crop_advisory.json')]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    advisory = json.load(f)
                result = [a for a in advisory if a.get('crop', '').lower() == crop.lower()]
                if result:
                    item = result[0]
                    if lang != 'en':
                        # Translate advisory fields
                        for field in ['season', 'soil', 'varieties', 'fertilizer', 'irrigation']:
                            if field in item:
                                item[field] = translator.translate_text(item[field], lang)
                    return jsonify(item)
                return jsonify({"error": f"No advisory found for {crop}"}), 404
        return jsonify({"error": "Advisory file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        query = data.get('query', '')
        # Accept explicit language from frontend (the selected UI language)
        ui_lang = data.get('lang', 'en')

        if not query:
            return jsonify({"error": "No query provided"}), 400

        # ── Step 1: Translate query to English ───────────────────────────────
        english_query, detected_lang = translator.translate_to_english(query)
        combined = english_query.lower() + ' ' + query.lower()

        # Decide final response language:
        # If the UI is set to a specific language, use that.
        # Otherwise fall back to the detected language of the query.
        response_lang = ui_lang if ui_lang != 'en' else detected_lang

        # ── Step 2: Intent detection ─────────────────────────────────────────
        intent = 'general'
        if any(w in combined for w in ['price', 'rate', 'cost', 'market', 'mandi', 'bhav', 'भाव', 'दाम', 'ਭਾਅ', 'விலை', 'ధర']):
            intent = 'market_price'
        elif any(w in combined for w in ['scheme', 'yojana', 'subsidy', 'sarkari', 'योजना', 'सब्सिडी', 'ਯੋਜਨਾ', 'திட்டம்']):
            intent = 'scheme'
        elif any(w in combined for w in ['disease', 'spot', 'yellow', 'brown', 'blight', 'fungus', 'pest', 'रोग', 'कीट', 'நோய்', 'వ్యాధి']):
            intent = 'disease'
        elif any(w in combined for w in ['grow', 'plant', 'fertilizer', 'sow', 'harvest', 'advisory', 'खाद', 'बुवाई', 'फसल', 'ಬೆಳೆ', 'పంట']):
            intent = 'advisory'

        # ── Step 3: Entity detection ─────────────────────────────────────────
        entities = {}
        detected_crop  = detect_crop(combined)
        detected_state = detect_state(combined)

        if detected_crop:
            entities['crop'] = detected_crop
        if detected_state:
            entities['state'] = detected_state

        # ── Step 4: Response generation (always in English first) ────────────
        response = ""

        if intent == 'market_price':
            if not detected_crop:
                available = get_available_crops()
                available_str = ', '.join(str(c).title() for c in available[:12])
                query_words = [w for w in english_query.lower().split()
                               if w not in ['price', 'of', 'in', 'the', 'what', 'is', 'rate',
                                            'cost', 'market', 'mandi', 'tell', 'me', 'today', 'current']
                               and len(w) > 2]
                unknown_crop = query_words[0].title() if query_words else 'That crop'
                response  = f"😕 Sorry, **{unknown_crop}** is not in my database.\n\n"
                response += f"📦 **Available crops:** {available_str}\n\n"
                response += f"💡 *Try: 'onion price in Maharashtra' or 'wheat rate in Punjab'*"

            elif detected_crop:
                if not detected_state:
                    response  = f"📍 Please specify a state to get accurate prices for **{detected_crop.title()}**.\n\n"
                    response += f"💡 *Try: '{detected_crop} price in Maharashtra' or '{detected_crop} price in Punjab'*"
                else:
                    price_result = price_analyzer.get_crop_price(detected_crop, detected_state)
                    err = price_result.get('error', '')

                    if err == 'crop_not_found':
                        available = price_result.get('available_crops', get_available_crops())
                        available_str = ', '.join(str(c).title() for c in available[:12])
                        response  = f"😕 Sorry, **{detected_crop.title()}** is not in my database.\n\n"
                        response += f"📦 **Available crops:** {available_str}\n\n"
                        response += f"💡 *Try: 'onion price in Maharashtra' or 'wheat rate in Punjab'*"

                    elif err == 'state_not_found':
                        available_states = price_result.get('available_states', [])
                        states_str = ', '.join(str(s).title() for s in available_states[:10])
                        response  = f"😕 Sorry, **{detected_crop.title()}** data is not available for **{detected_state.title()}**.\n\n"
                        response += f"🗺️ **States available for {detected_crop.title()}:** {states_str}\n\n"
                        response += f"💡 *Try: '{detected_crop} price in {available_states[0].title() if available_states else 'Maharashtra'}'*"

                    elif 'error' not in price_result:
                        response  = f"📊 **{price_result['crop'].title()} Market Price in {price_result['state'].title()}**\n\n"
                        response += f"💰 **Modal Price:** ₹{price_result['modal_price']}/quintal\n"
                        response += f"📉 **Min Price:** ₹{price_result['min_price']}/quintal\n"
                        response += f"📈 **Max Price:** ₹{price_result['max_price']}/quintal\n"
                        response += f"📍 **Market:** {price_result['market']}\n"
                        response += f"🗺️ **State:** {price_result['state']}\n"
                        response += f"📅 **Date:** {price_result['date']}\n"
                        if price_result.get('arrival_quantity'):
                            response += f"📦 **Arrival:** {price_result['arrival_quantity']} quintals\n"
                    else:
                        response = "😕 Could not fetch price data. Please try again with a clearer crop and state name."

        elif intent == 'scheme':
            try:
                schemes_path = os.path.join(RAW_DATA_DIR, 'schemes.json')
                if os.path.exists(schemes_path):
                    with open(schemes_path, 'r', encoding='utf-8') as f:
                        schemes = json.load(f)
                    if schemes:
                        response = "📋 **Government Schemes for Farmers:**\n\n"
                        for i, scheme in enumerate(schemes[:3], 1):
                            response += f"{i}. **{scheme.get('name', 'Scheme')}**\n"
                            response += f"   {scheme.get('description', '')[:120]}...\n\n"
                        response += "*Type 'more schemes' to see all available schemes.*"
                    else:
                        response = "No schemes found in database."
                else:
                    response = "Scheme information coming soon! Check back later."
            except:
                response = "Scheme information coming soon!"

        elif intent == 'advisory':
            if detected_crop:
                try:
                    advisory_path = os.path.join(RAW_DATA_DIR, 'crop_advisory.json')
                    if os.path.exists(advisory_path):
                        with open(advisory_path, 'r', encoding='utf-8') as f:
                            advisories = json.load(f)
                        crop_advice = next((a for a in advisories if a.get('crop', '').lower() == detected_crop.lower()), None)
                        if crop_advice:
                            response = f"🌱 **{detected_crop.title()} Growing Guide:**\n\n"
                            if 'season' in crop_advice:
                                response += f"📅 **Season:** {crop_advice['season']}\n"
                            if 'soil' in crop_advice:
                                response += f"🪴 **Soil:** {crop_advice['soil']}\n"
                            if 'varieties' in crop_advice:
                                response += f"🌾 **Varieties:** {crop_advice['varieties']}\n"
                            if 'fertilizer' in crop_advice:
                                response += f"🧪 **Fertilizer:** {crop_advice['fertilizer']}\n"
                            if 'irrigation' in crop_advice:
                                response += f"💧 **Irrigation:** {crop_advice['irrigation']}\n"
                        else:
                            response = f"Advisory for **{detected_crop.title()}** is coming soon! Please consult your local Krishi Vigyan Kendra."
                    else:
                        response = "Advisory data not found. Please consult your local agricultural officer."
                except Exception as e:
                    response = f"Advisory for **{detected_crop.title()}** coming soon!"
            else:
                response = "Please specify a crop name for advisory. For example: *'How to grow tomatoes?'* or *'wheat fertilizer advice'*"

        elif intent == 'disease':
            response = "🔍 **Disease Detection**\n\nPlease upload a photo of your plant using the 📷 camera button in the input box below.\n\nI will analyze it and identify any diseases along with treatment recommendations."

        else:
            if any(w in combined for w in ['hi', 'hello', 'namaste', 'hey', 'नमस्ते', 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ', 'வணக்கம்', 'నమస్కారం']):
                available = get_available_crops()
                available_str = ', '.join(c.title() for c in available[:8])
                response  = "👋 **Namaste! I'm FarmBuddy**, your AI farming assistant.\n\n"
                response += "I can help you with:\n"
                response += "• 🌾 **Crop prices** — *'onion price in Assam'*\n"
                response += "• 📋 **Government schemes** — *'show farmer schemes'*\n"
                response += "• 🌱 **Farming advice** — *'how to grow wheat?'*\n"
                response += "• 🔍 **Disease detection** — upload a plant photo\n\n"
                response += f"📦 **Available price data for:** {available_str}"
            else:
                response  = "I'm not sure I understood that. Try asking:\n"
                response += "• **Market prices:** *'onion price in Maharashtra'*\n"
                response += "• **Government schemes:** *'show me farmer schemes'*\n"
                response += "• **Crop advice:** *'how to grow tomatoes?'*\n"
                response += "• **Disease detection:** Upload a plant photo using the 📷 button"

        # ── Step 5: Translate response to target language ─────────────────────
        if response_lang and response_lang != 'en':
            response = translator.translate_response(response, response_lang)

        return jsonify({
            'original_query': query,
            'detected_language': detected_lang,
            'response_language': response_lang,
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

        ext      = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"upload_{int(time.time())}.{ext}"
        temp_path = os.path.join(UPLOAD_DIR, filename)
        file.save(temp_path)

        if not os.path.exists(temp_path):
            return jsonify({"error": "Failed to save image"}), 500

        result = disease_predictor.predict(temp_path)

        # Translate treatment if language param is passed
        lang = request.form.get('lang', 'en')
        if lang != 'en' and 'treatment' in result:
            result['treatment'] = translator.translate_text(result['treatment'], lang)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/translate', methods=['POST'])
def translate_text_api():
    """
    General-purpose translation endpoint.
    Used by frontend for fallback response translation.
    """
    try:
        data = request.json
        text = data.get('text', '')
        target_lang = data.get('target_lang', 'en')
        if not text or target_lang == 'en':
            return jsonify({'translated_text': text})
        return jsonify({'translated_text': translator.translate_text(text, target_lang)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crops', methods=['GET'])
def get_available_crops_api():
    return jsonify({"crops": get_available_crops()})


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "FarmBuddy API is running",
        "supported_languages": list(translator.supported_languages.keys()),
        "available_crops": get_available_crops(),
        "paths": {
            "project_root": PROJECT_ROOT,
            "data_dir": DATA_DIR,
            "upload_dir": UPLOAD_DIR
        }
    })


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "FarmBuddy API is running",
        "endpoints": [
            "/api/health",
            "/api/crops",
            "/api/price?crop=onion&state=assam",
            "/api/schemes",
            "/api/faqs?lang=hi",
            "/api/predict-disease (POST)",
            "/api/chat (POST) — accepts {query, lang}",
            "/api/translate (POST) — accepts {text, target_lang}"
        ]
    })


if __name__ == '__main__':
    print("🚀 FarmBuddy Backend Starting...")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"📦 Available crops: {get_available_crops()}")
    print(f"🌐 Supported languages: {list(translator.supported_languages.keys())}")
    print(f"🌐 Server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)