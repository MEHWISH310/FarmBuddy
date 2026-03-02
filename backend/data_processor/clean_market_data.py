import pandas as pd
import os
import glob

class MarketDataCleaner:
    def __init__(self):
        self.raw_dir = "data/market_data"
        self.processed_dir = "data/processed_data"
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def clean_csv_file(self, file_path):
        print(f"Cleaning: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path, skiprows=1)
        
        for col in ['Min Price', 'Max Price', 'Modal Price']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
        
        if 'Arrival Quantity' in df.columns:
            df['Arrival Quantity'] = pd.to_numeric(df['Arrival Quantity'], errors='coerce')
        
        df['download_date'] = pd.Timestamp.now().date()
        return df
    
    def process_all_files(self):
        all_files = glob.glob(os.path.join(self.raw_dir, "*.csv"))
        print(f"Found {len(all_files)} files to process")
        
        for file in all_files:
            try:
                df = self.clean_csv_file(file)
                filename = os.path.basename(file)
                output_path = os.path.join(self.processed_dir, f"cleaned_{filename}")
                df.to_csv(output_path, index=False)
                print(f"Saved: cleaned_{filename} ({len(df)} records)")
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    def create_unified_dataset(self):
        all_files = glob.glob(os.path.join(self.processed_dir, "cleaned_*.csv"))
        
        if not all_files:
            print("No cleaned files found")
            return
        
        dfs = []
        for file in all_files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        unified_df = pd.concat(dfs, ignore_index=True)
        unified_df['Arrival Date'] = pd.to_datetime(unified_df['Arrival Date'], format='%d-%m-%Y')
        unified_df = unified_df.sort_values('Arrival Date')
        
        output_path = os.path.join(self.processed_dir, "market_prices_all_crops.csv")
        unified_df.to_csv(output_path, index=False)
        
        print(f"\nUnified dataset created: {output_path}")
        print(f"Total records: {len(unified_df)}")
        print(f"Crops: {unified_df['Commodity'].nunique()}")
        print(f"States: {unified_df['State'].nunique()}")
        print(f"Date range: {unified_df['Arrival Date'].min()} to {unified_df['Arrival Date'].max()}")
        
        return unified_df

if __name__ == "__main__":
    cleaner = MarketDataCleaner()
    cleaner.process_all_files()
    unified = cleaner.create_unified_dataset()