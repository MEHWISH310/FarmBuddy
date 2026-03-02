import pandas as pd
import os

def test_your_data():
    almond_path = "data/market_data/Almond.csv"
    
    if os.path.exists(almond_path):
        df = pd.read_csv(almond_path, skiprows=1)
        
        for col in ['Min Price', 'Max Price', 'Modal Price']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
        
        return {
            'total_records': len(df),
            'min_price': float(df['Min Price'].min()),
            'max_price': float(df['Max Price'].max()),
            'avg_price': float(df['Modal Price'].mean())
        }
    else:
        return {'error': 'Almond.csv not found'}

if __name__ == "__main__":
    test_your_data()