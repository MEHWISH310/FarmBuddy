import re

class IntentClassifier:
    def __init__(self):
        self.intents = {
            'market_price': {
                'keywords': ['price', 'rate', 'cost', 'mandi', 'bhav', 'kitna', 'रेत', 'भाव', 'दाम'],
                'patterns': [
                    r'(price|rate|cost).*(wheat|rice|onion|tomato|potato)',
                    r'(wheat|rice|onion|tomato|potato).*(price|rate|cost)',
                    r'(\w+)\s+का\s+भाव',
                    r'(\w+)\s+விலை'
                ]
            },
            'disease': {
                'keywords': ['disease', 'problem', 'spot', 'yellow', 'brown', 'leaves', 
                           'रोग', 'धब्बा', 'पीला', 'बीमारी', 'நோய்'],
                'patterns': [
                    r'(disease|problem).*(crop|plant|leaf|leaves)',
                    r'(leaf|leaves).*(yellow|brown|spot)',
                    r'(\w+)\s+में\s+रोग',
                    r'(\w+)\s+நோய்'
                ]
            },
            'scheme': {
                'keywords': ['scheme', 'yojana', 'subsidy', 'loan', 'pension', 'kisan', 
                           'योजना', 'सब्सिडी', 'कर्ज', 'திட்டம்'],
                'patterns': [
                    r'(pm|kisan|government).*(scheme|yojana)',
                    r'(scheme|yojana).*(farmer|kisan)',
                    r'(\w+)\s+योजना',
                    r'(\w+)\s+திட்டம்'
                ]
            },
            'weather': {
                'keywords': ['weather', 'rain', 'temperature', 'mausam', 'बारिश', 'मौसम', 'வானிலை'],
                'patterns': [
                    r'(weather|rain).*(today|tomorrow)',
                    r'(temperature|mausam).*(\w+)',
                    r'(\w+)\s+में\s+मौसम'
                ]
            },
            'advisory': {
                'keywords': ['advice', 'suggest', 'how to', 'tips', 'recommend', 
                           'सलाह', 'कैसे', 'ஆலோசனை'],
                'patterns': [
                    r'how to (grow|plant|cultivate) (\w+)',
                    r'(best|good) (fertilizer|pesticide) for (\w+)',
                    r'(\w+)\s+की\s+खेती\s+कैसे'
                ]
            },
            'general': {
                'keywords': ['hello', 'hi', 'thank', 'help', 'namaste', 'नमस्ते'],
                'patterns': []
            }
        }
    
    def predict_intent(self, text):
        text_lower = text.lower()
        for intent, data in self.intents.items():
            for keyword in data['keywords']:
                if keyword.lower() in text_lower:
                    return intent, 0.8
        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return intent, 0.9
        return 'general', 0.5
    
    def get_all_intents(self):
        return list(self.intents.keys())