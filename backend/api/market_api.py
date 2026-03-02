from flask import Flask, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processor.analyze_prices import PriceAnalyzer

app = Flask(__name__)
analyzer = PriceAnalyzer()

@app.route('/api/price', methods=['GET'])
def get_price():
    crop = request.args.get('crop')
    state = request.args.get('state')
    market = request.args.get('market')
    
    if not crop:
        return jsonify({"error": "Please provide crop name"}), 400
    
    result = analyzer.get_crop_price(crop, state, market)
    return jsonify(result)

@app.route('/api/trend', methods=['GET'])
def get_trend():
    crop = request.args.get('crop')
    state = request.args.get('state')
    days = int(request.args.get('days', 30))
    
    if not crop or not state:
        return jsonify({"error": "Please provide crop and state"}), 400
    
    trend = analyzer.get_price_trend(crop, state, days)
    return jsonify(trend)

@app.route('/api/report', methods=['GET'])
def get_report():
    report = analyzer.generate_report()
    return jsonify(report)

if __name__ == '__main__':
    app.run(debug=True, port=5000)