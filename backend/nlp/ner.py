import re
import json

class AgriculturalNER:
    def __init__(self):
        # Crop database
        self.crops = [
            'wheat', 'rice', 'onion', 'potato', 'tomato', 'bajra', 'maize',
            'barley', 'sunflower', 'almond', 'arhar', 'masoor', 'moong',
            'gram', 'mustard', 'groundnut', 'soybean', 'cotton', 'sugarcane',
            'गेहूं', 'चावल', 'प्याज', 'आलू', 'टमाटर', 'बाजरा', 'मक्का',
            'கோதுமை', 'நெல்', 'வெங்காயம்', 'உருளைக்கிழங்கு', 'தக்காளி'
        ]
        
        # State database
        self.states = [
            'uttar pradesh', 'punjab', 'haryana', 'maharashtra', 'tamil nadu',
            'karnataka', 'gujarat', 'rajasthan', 'bihar', 'west bengal',
            'madhya pradesh', 'andhra pradesh', 'telangana', 'odisha',
            'उत्तर प्रदेश', 'पंजाब', 'हरियाणा', 'महाराष्ट्र', 'तमिलनाडु',
            'தமிழ்நாடு', 'கர்நாடகா', 'மகாராஷ்டிரா'
        ]
        
        # Market database
        self.markets = [
            'mumbai', 'delhi', 'chennai', 'kolkata', 'pune', 'ludhiana',
            'agra', 'kanpur', 'lucknow', 'nagpur', 'नागपुर', 'लखनऊ',
            'சென்னை', 'மும்பை', 'டெல்லி'
        ]
        
        # Disease keywords
        self.diseases = [
            'blight', 'rust', 'mildew', 'spot', 'wilt', 'mosaic', 'virus',
            'fungus', 'bacterial', 'yellow', 'झुलसा', 'रतुआ', 'फफूंदी',
            'பூஞ்சை', 'துரு', 'கருகல்'
        ]
    
    def extract_entities(self, text):
        """Extract agricultural entities from text"""
        text_lower = text.lower()
        entities = {
            'crop': [],
            'state': [],
            'market': [],
            'disease': []
        }
        
        # Extract crops
        for crop in self.crops:
            if crop.lower() in text_lower:
                if crop not in entities['crop']:
                    entities['crop'].append(crop)
        
        # Extract states
        for state in self.states:
            if state.lower() in text_lower:
                if state not in entities['state']:
                    entities['state'].append(state)
        
        # Extract markets
        for market in self.markets:
            if market.lower() in text_lower:
                if market not in entities['market']:
                    entities['market'].append(market)
        
        # Extract diseases
        for disease in self.diseases:
            if disease.lower() in text_lower:
                if disease not in entities['disease']:
                    entities['disease'].append(disease)
        
        # Extract numbers (prices, quantities)
        price_pattern = r'₹?(\d+[,]?\d*)\s*(?:per|/)?\s*(kg|quintal|ton)'
        prices = re.findall(price_pattern, text)
        if prices:
            entities['price'] = prices
        
        return entities
    
    def get_primary_crop(self, text):
        """Get the main crop mentioned"""
        entities = self.extract_entities(text)
        if entities['crop']:
            return entities['crop'][0]
        return None
    
    def get_location(self, text):
        """Get location (state/market) mentioned"""
        entities = self.extract_entities(text)
        if entities['state']:
            return entities['state'][0]
        if entities['market']:
            return entities['market'][0]
        return None