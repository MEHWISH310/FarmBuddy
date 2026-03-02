import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta

class PriceAnalyzer:
    def __init__(self):
        # Get the project root directory
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from data_processor to backend to FarmBuddy
        self.project_root = os.path.dirname(os.path.dirname(self.current_dir))
        
        # Correct path to your processed data file
        self.data_path = os.path.join(self.project_root, 'data', 'processed_data', 'market_prices_all_crops.csv')
        
        # Also store paths to individual crop files for fallback
        self.market_data_dir = os.path.join(self.project_root, 'data', 'market_data')
        
        # Load data on initialization
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load market data from CSV file"""
        try:
            # Try to load the combined CSV first
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
                print(f"✅ Loaded market data: {len(self.df)} records from {self.data_path}")
                
                # Standardize column names (handle different possible formats)
                self.standardize_columns()
                
                # Convert date column to datetime
                if 'Arrival Date' in self.df.columns:
                    self.df['Arrival Date'] = pd.to_datetime(self.df['Arrival Date'], format='%d-%m-%Y', errors='coerce')
                elif 'date' in self.df.columns:
                    self.df['Arrival Date'] = pd.to_datetime(self.df['date'], format='%d-%m-%Y', errors='coerce')
                    
                return True
            else:
                print(f"⚠️ Market data file not found at: {self.data_path}")
                print("Attempting to create from individual crop files...")
                return self.create_combined_data()
                
        except Exception as e:
            print(f"❌ Error loading market data: {e}")
            self.df = pd.DataFrame()
            return False
    
    def standardize_columns(self):
        """Standardize column names to expected format"""
        column_mapping = {
            'commodity': 'Commodity',
            'crop': 'Commodity',
            'state': 'State',
            'market': 'Market',
            'district': 'District',
            'min_price': 'Min Price',
            'max_price': 'Max Price',
            'modal_price': 'Modal Price',
            'price': 'Modal Price',
            'arrival_date': 'Arrival Date',
            'date': 'Arrival Date',
            'arrival_quantity': 'Arrival Quantity',
            'quantity': 'Arrival Quantity'
        }
        
        self.df.columns = [col.strip() for col in self.df.columns]
        self.df.rename(columns=column_mapping, inplace=True, errors='ignore')
    
    def create_combined_data(self):
        """Create combined dataset from individual crop CSV files"""
        try:
            if os.path.exists(self.market_data_dir):
                all_files = [f for f in os.listdir(self.market_data_dir) if f.endswith('.csv')]
                data_frames = []
                
                for file in all_files:
                    file_path = os.path.join(self.market_data_dir, file)
                    crop_name = file.replace('.csv', '')
                    
                    try:
                        df_crop = pd.read_csv(file_path)
                        if 'Commodity' not in df_crop.columns:
                            df_crop['Commodity'] = crop_name
                        data_frames.append(df_crop)
                        print(f"  ✅ Loaded: {file}")
                    except Exception as e:
                        print(f"  ❌ Error loading {file}: {e}")
                
                if data_frames:
                    self.df = pd.concat(data_frames, ignore_index=True)
                    self.standardize_columns()
                    
                    # Save combined data for future use
                    os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
                    self.df.to_csv(self.data_path, index=False)
                    print(f"✅ Created combined market data with {len(self.df)} records")
                    return True
                else:
                    print("❌ No individual crop files found")
                    return False
            else:
                print(f"❌ Market data directory not found: {self.market_data_dir}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating combined data: {e}")
            return False
    
    def get_crop_price(self, crop, state=None, market=None):
        """Get latest price for a specific crop"""
        try:
            if self.df is None or len(self.df) == 0:
                if not self.load_data():
                    return {"error": "Market data not available"}
            
            # Create mask for filtering
            mask = self.df['Commodity'].str.contains(crop, case=False, na=False)
            
            if state:
                mask &= self.df['State'].str.contains(state, case=False, na=False)
            
            if market:
                mask &= self.df['Market'].str.contains(market, case=False, na=False)
            
            result = self.df[mask].copy()
            
            if len(result) == 0:
                # Try more flexible search
                crop_words = crop.lower().split()
                for word in crop_words:
                    if len(word) > 3:  # Only search with significant words
                        mask = self.df['Commodity'].str.contains(word, case=False, na=False)
                        result = self.df[mask].copy()
                        if len(result) > 0:
                            break
                
                if len(result) == 0:
                    return {
                        "error": f"No data found for '{crop}'",
                        "available_crops": self.get_available_crops()[:10]
                    }
            
            # Ensure date is datetime
            if 'Arrival Date' not in result.columns:
                result['Arrival Date'] = pd.Timestamp.now()
            
            # Get latest record
            result = result.sort_values('Arrival Date', ascending=False)
            latest = result.iloc[0]
            
            # Handle missing values
            def safe_float(val, default=0):
                try:
                    return float(val) if pd.notna(val) else default
                except:
                    return default
            
            return {
                "success": True,
                "crop": str(latest.get('Commodity', crop)),
                "state": str(latest.get('State', state or 'Unknown')),
                "market": str(latest.get('Market', market or 'Unknown')),
                "district": str(latest.get('District', 'Unknown')),
                "date": str(latest['Arrival Date'].date()) if pd.notna(latest['Arrival Date']) else datetime.now().strftime('%Y-%m-%d'),
                "min_price": safe_float(latest.get('Min Price')),
                "max_price": safe_float(latest.get('Max Price')),
                "modal_price": safe_float(latest.get('Modal Price')),
                "arrival_quantity": safe_float(latest.get('Arrival Quantity')),
                "unit": "Rs/quintal"  # Default unit
            }
            
        except Exception as e:
            return {"error": f"Error processing price data: {str(e)}"}
    
    def get_price_trend(self, crop, state, days=30):
        """Get price trend for a crop over specified days"""
        try:
            if self.df is None or len(self.df) == 0:
                if not self.load_data():
                    return {"error": "Market data not available"}
            
            mask = (self.df['Commodity'].str.contains(crop, case=False, na=False)) & \
                   (self.df['State'].str.contains(state, case=False, na=False))
            
            trend_data = self.df[mask].copy()
            
            if len(trend_data) == 0:
                return {"error": f"No trend data found for {crop} in {state}"}
            
            # Ensure date is datetime
            trend_data['Arrival Date'] = pd.to_datetime(trend_data['Arrival Date'], errors='coerce')
            trend_data = trend_data.dropna(subset=['Arrival Date'])
            trend_data = trend_data.sort_values('Arrival Date')
            
            # Get last 'days' records
            trend_data = trend_data.tail(days)
            
            # Calculate statistics
            result = []
            for _, row in trend_data.iterrows():
                result.append({
                    "date": row['Arrival Date'].strftime('%Y-%m-%d'),
                    "modal_price": float(row.get('Modal Price', 0)) if pd.notna(row.get('Modal Price')) else 0,
                    "min_price": float(row.get('Min Price', 0)) if pd.notna(row.get('Min Price')) else 0,
                    "max_price": float(row.get('Max Price', 0)) if pd.notna(row.get('Max Price')) else 0,
                    "market": str(row.get('Market', 'Unknown'))
                })
            
            # Add summary
            if len(result) > 0:
                prices = [r['modal_price'] for r in result if r['modal_price'] > 0]
                if prices:
                    summary = {
                        "average_price": sum(prices) / len(prices),
                        "highest_price": max(prices),
                        "lowest_price": min(prices),
                        "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                        "trend": "up" if len(prices) > 1 and prices[-1] > prices[0] else "down" if len(prices) > 1 else "stable"
                    }
                    return {
                        "data": result,
                        "summary": summary
                    }
            
            return result
            
        except Exception as e:
            return {"error": f"Error processing trend data: {str(e)}"}
    
    def generate_report(self):
        """Generate summary report of market data"""
        try:
            if self.df is None or len(self.df) == 0:
                if not self.load_data():
                    return {"error": "Market data not available"}
            
            # Basic statistics
            report = {
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_records": len(self.df),
                "crops": int(self.df['Commodity'].nunique()),
                "states": int(self.df['State'].nunique()) if 'State' in self.df.columns else 0,
                "markets": int(self.df['Market'].nunique()) if 'Market' in self.df.columns else 0,
            }
            
            # Date range
            if 'Arrival Date' in self.df.columns:
                valid_dates = self.df['Arrival Date'].dropna()
                if len(valid_dates) > 0:
                    report['date_range'] = {
                        "from": valid_dates.min().strftime('%Y-%m-%d'),
                        "to": valid_dates.max().strftime('%Y-%m-%d')
                    }
            
            # Average prices by crop
            if 'Modal Price' in self.df.columns:
                avg_prices = self.df.groupby('Commodity')['Modal Price'].mean().sort_values(ascending=False)
                report['avg_price_by_crop'] = {k: float(v) for k, v in avg_prices.head(10).items() if pd.notna(v)}
            
            # Top markets by volume
            if 'Market' in self.df.columns:
                top_markets = self.df['Market'].value_counts().head(10)
                report['top_markets'] = {k: int(v) for k, v in top_markets.items()}
            
            # Price ranges
            if 'Modal Price' in self.df.columns:
                valid_prices = self.df['Modal Price'].dropna()
                if len(valid_prices) > 0:
                    report['price_range'] = {
                        "min": float(valid_prices.min()),
                        "max": float(valid_prices.max()),
                        "average": float(valid_prices.mean())
                    }
            
            return report
            
        except Exception as e:
            return {"error": f"Error generating report: {str(e)}"}
    
    def get_available_crops(self, limit=50):
        """Get list of available crops in the dataset"""
        try:
            if self.df is None or len(self.df) == 0:
                return []
            
            crops = self.df['Commodity'].dropna().unique()
            return sorted([str(c) for c in crops])[:limit]
        except:
            return []
    
    def get_available_states(self, crop=None):
        """Get list of available states for a crop"""
        try:
            if self.df is None or len(self.df) == 0:
                return []
            
            if crop:
                mask = self.df['Commodity'].str.contains(crop, case=False, na=False)
                states = self.df[mask]['State'].dropna().unique()
            else:
                states = self.df['State'].dropna().unique()
            
            return sorted([str(s) for s in states])
        except:
            return []
    
    def search_by_price_range(self, min_price, max_price, state=None):
        """Search crops within a price range"""
        try:
            if self.df is None or len(self.df) == 0:
                return {"error": "Data not available"}
            
            mask = (self.df['Modal Price'] >= min_price) & (self.df['Modal Price'] <= max_price)
            
            if state:
                mask &= self.df['State'].str.contains(state, case=False, na=False)
            
            results = self.df[mask].copy()
            results = results.sort_values('Modal Price')
            
            return results[['Commodity', 'State', 'Market', 'Modal Price']].drop_duplicates().head(20).to_dict('records')
            
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Test the analyzer
    analyzer = PriceAnalyzer()
    
    print("\n" + "="*50)
    print("FARMBUDDY PRICE ANALYZER TEST")
    print("="*50)
    
    # Test 1: Get price for a crop
    print("\n📊 Test 1: Get Onion price in Maharashtra")
    price = analyzer.get_crop_price("Onion", "Maharashtra")
    print(price)
    
    # Test 2: Get price trend
    print("\n📈 Test 2: Get Wheat price trend in Punjab")
    trend = analyzer.get_price_trend("Wheat", "Punjab", days=7)
    print(trend)
    
    # Test 3: Generate report
    print("\n📋 Test 3: Generate market report")
    report = analyzer.generate_report()
    print(report)
    
    # Test 4: Available crops
    print("\n🌾 Test 4: Available crops")
    crops = analyzer.get_available_crops(10)
    print(crops)