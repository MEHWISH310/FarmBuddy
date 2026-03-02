import pandas as pd
import os

def test_your_data():
    almond_path = "data/market_data/Almond.csv"
    
    if os.path.exists(almond_path):
        print("Almond.csv found!")
        df = pd.read_csv(almond_path, skiprows=1)
        
        # Convert price columns to numbers
        for col in ['Min Price', 'Max Price', 'Modal Price']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
        
        print(f"\nData Summary:")
        print(f"Total records: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df['Arrival Date'].min()} to {df['Arrival Date'].max()}")
        
        print(f"\nPrice range:")
        print(f"Min: {df['Min Price'].min()}")
        print(f"Max: {df['Max Price'].max()}")
        print(f"Avg: {df['Modal Price'].mean():.2f}")
    else:
        print("Almond.csv not found")

if __name__ == "__main__":
    test_your_data()