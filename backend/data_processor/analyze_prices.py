import pandas as pd
import os

class PriceAnalyzer:
    def __init__(self):
        self.data_path = "data/processed_data/market_prices_all_crops.csv"
        
    def get_crop_price(self, crop, state=None, market=None):
        df = pd.read_csv(self.data_path)
        
        mask = df['Commodity'].str.contains(crop, case=False, na=False)
        
        if state:
            mask &= df['State'].str.contains(state, case=False, na=False)
        
        if market:
            mask &= df['Market'].str.contains(market, case=False, na=False)
        
        result = df[mask]
        
        if len(result) == 0:
            return {"error": f"No data found for {crop}"}
        
        result['Arrival Date'] = pd.to_datetime(result['Arrival Date'], format='%d-%m-%Y')
        latest = result.sort_values('Arrival Date', ascending=False).iloc[0]
        
        return {
            "crop": latest['Commodity'],
            "state": latest['State'],
            "market": latest['Market'],
            "date": latest['Arrival Date'].strftime('%Y-%m-%d'),
            "min_price": float(latest['Min Price']),
            "max_price": float(latest['Max Price']),
            "modal_price": float(latest['Modal Price']),
            "arrival_quantity": float(latest['Arrival Quantity'])
        }
    
    def get_price_trend(self, crop, state, days=30):
        df = pd.read_csv(self.data_path)
        
        mask = (df['Commodity'].str.contains(crop, case=False, na=False)) & \
               (df['State'].str.contains(state, case=False, na=False))
        
        df = df[mask].copy()
        df['Arrival Date'] = pd.to_datetime(df['Arrival Date'], format='%d-%m-%Y')
        df = df.sort_values('Arrival Date')
        df = df.tail(days)
        
        return df[['Arrival Date', 'Modal Price', 'Min Price', 'Max Price']].to_dict('records')
    
    def generate_report(self):
        df = pd.read_csv(self.data_path)
        
        report = {
            "total_records": len(df),
            "crops": df['Commodity'].nunique(),
            "states": df['State'].nunique(),
            "markets": df['Market'].nunique(),
            "date_range": f"{df['Arrival Date'].min()} to {df['Arrival Date'].max()}",
            "avg_price_by_crop": df.groupby('Commodity')['Modal Price'].mean().to_dict(),
            "top_markets": df.groupby('Market').size().sort_values(ascending=False).head(10).to_dict()
        }
        
        return report

if __name__ == "__main__":
    analyzer = PriceAnalyzer()
    price = analyzer.get_crop_price("Almond", "Maharashtra")
    print(price)
    report = analyzer.generate_report()
    print(report)