import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor.analyze_prices import PriceAnalyzer
from nlp.translator import LanguageTranslator

class ResponseGenerator:
    def __init__(self):
        self.price_analyzer = PriceAnalyzer()
        self.translator = LanguageTranslator()
        self.load_data()
    
    def load_data(self):
        try:
            with open('data/schemes.json', 'r', encoding='utf-8') as f:
                self.schemes = json.load(f)
        except:
            self.schemes = []
        
        try:
            with open('data/raw_data/faq_dataset.json', 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
        except:
            self.faqs = []
        
        try:
            with open('data/raw_data/crop_advisory.json', 'r', encoding='utf-8') as f:
                self.advisory = json.load(f)
        except:
            self.advisory = []
    
    def generate_response(self, query, intent, entities, language='en'):
        response = ""
        
        if intent == 'market_price':
            response = self.handle_market_price(entities)
        elif intent == 'disease':
            response = self.handle_disease(entities)
        elif intent == 'scheme':
            response = self.handle_scheme(entities)
        elif intent == 'weather':
            response = self.handle_weather(entities)
        elif intent == 'advisory':
            response = self.handle_advisory(entities)
        else:
            response = self.handle_general()
        
        if language != 'en':
            response = self.translator.translate_text(response, language)
        
        return response
    
    def handle_market_price(self, entities):
        crop = entities.get('crop', [None])
        state = entities.get('state', [None])
        
        if not crop or not crop[0]:
            return "Please tell me which crop price you want to know."
        
        crop_name = crop[0]
        state_name = state[0] if state and state[0] else None
        
        price_data = self.price_analyzer.get_crop_price(crop_name, state_name)
        
        if 'error' in price_data:
            return f"Sorry, no price data found for {crop_name}."
        
        location = price_data.get('state', 'your region')
        date = price_data.get('date', 'recent date')
        price = price_data.get('modal_price', 'N/A')
        
        return f"{crop_name.title()} price in {location} on {date} is ₹{price} per quintal."
    
    def handle_disease(self, entities):
        crop = entities.get('crop', [None])
        disease = entities.get('disease', [None])
        
        if crop and crop[0]:
            return f"For {crop[0]} diseases, please upload a photo of the affected plant for accurate detection."
        
        return "Please upload a photo of your crop for disease detection, or describe the symptoms."
    
    def handle_scheme(self, entities):
        if not self.schemes:
            return "Scheme information is currently being updated."
        
        query_text = entities.get('text', '').lower()
        for scheme in self.schemes:
            if scheme['name'].lower() in query_text:
                return f"{scheme['name']}: {scheme['description']}\nBenefit: {scheme['benefit']}\nApply: {scheme['how_to_apply']}"
        
        top_schemes = self.schemes[:3]
        response = "Popular government schemes:\n"
        for s in top_schemes:
            response += f"• {s['name']}: {s['description']}\n"
        response += "\nAsk about specific scheme like PM-KISAN for more details."
        return response
    
    def handle_weather(self, entities):
        location = entities.get('state', [None]) or entities.get('market', [None])
        loc_name = location[0] if location and location[0] else "your area"
        return f"Weather information for {loc_name} will be available soon. Currently, you can check market prices or crop advisory."
    
    def handle_advisory(self, entities):
        crop = entities.get('crop', [None])
        
        if not crop or not crop[0]:
            return "Please tell me which crop you need advisory for."
        
        crop_name = crop[0].lower()
        
        for adv in self.advisory:
            if adv.get('crop', '').lower() == crop_name:
                return (f"Crop: {adv['crop']}\n"
                       f"Season: {adv['season']}\n"
                       f"Sowing: {adv['sowing_time']}\n"
                       f"Fertilizer: {adv['fertilizer']}\n"
                       f"Yield: {adv['yield']}")
        
        return f"Advisory for {crop_name} is being updated. Please check later."
    
    def handle_general(self):
        return ("Hello! I'm FarmBuddy, your agricultural assistant.\n\n"
                "I can help you with:\n"
                "• Crop prices (e.g., 'onion price in maharashtra')\n"
                "• Government schemes (e.g., 'pm kisan details')\n"
                "• Disease detection (upload a photo)\n"
                "• Farming advice (e.g., 'wheat sowing time')\n\n"
                "How can I help you today?")