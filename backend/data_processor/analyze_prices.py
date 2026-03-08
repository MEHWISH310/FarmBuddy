import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta

class PriceAnalyzer:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(self.current_dir))
        self.data_path = os.path.join(self.project_root, 'data', 'processed_data', 'market_prices_all_crops.csv')
        self.market_data_dir = os.path.join(self.project_root, 'data', 'market_data')
        self.df = None
        self.load_data()

    def load_data(self):
        try:
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
                self.standardize_columns()
                if 'Commodity' in self.df.columns:
                    self.df['Commodity'] = self.df['Commodity'].str.replace(r'^Cleaned\s+', '', regex=True).str.strip()
                if 'Arrival Date' in self.df.columns:
                    self.df['Arrival Date'] = pd.to_datetime(self.df['Arrival Date'], format='%d-%m-%Y', errors='coerce')
                elif 'date' in self.df.columns:
                    self.df['Arrival Date'] = pd.to_datetime(self.df['date'], format='%d-%m-%Y', errors='coerce')
                return True
            else:
                return self.create_combined_data()
        except Exception as e:
            print(f"Error loading market data: {e}")
            self.df = pd.DataFrame()
            return False

    def standardize_columns(self):
        column_mapping = {
            'commodity': 'Commodity', 'crop': 'Commodity',
            'state': 'State', 'market': 'Market', 'district': 'District',
            'min_price': 'Min Price', 'max_price': 'Max Price',
            'modal_price': 'Modal Price', 'price': 'Modal Price',
            'arrival_date': 'Arrival Date', 'date': 'Arrival Date',
            'arrival_quantity': 'Arrival Quantity', 'quantity': 'Arrival Quantity'
        }
        self.df.columns = [col.strip() for col in self.df.columns]
        self.df.rename(columns=column_mapping, inplace=True, errors='ignore')

    def create_combined_data(self):
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
                    except Exception as e:
                        print(f"Error loading {file}: {e}")
                if data_frames:
                    self.df = pd.concat(data_frames, ignore_index=True)
                    self.standardize_columns()
                    os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
                    self.df.to_csv(self.data_path, index=False)
                    return True
            return False
        except Exception as e:
            print(f"Error creating combined data: {e}")
            return False

    def get_crop_price(self, crop, state=None, market=None):
        try:
            if self.df is None or len(self.df) == 0:
                if not self.load_data():
                    return {"error": "Market data not available"}

            crop_mask = self.df['Commodity'].str.contains(crop, case=False, na=False)
            crop_results = self.df[crop_mask].copy()

            if len(crop_results) == 0:
                crop_words = [w for w in crop.lower().split() if len(w) > 3]
                for word in crop_words:
                    crop_mask = self.df['Commodity'].str.contains(word, case=False, na=False)
                    crop_results = self.df[crop_mask].copy()
                    if len(crop_results) > 0:
                        break

            if len(crop_results) == 0:
                available = self.get_available_crops()
                return {
                    "error": "crop_not_found",
                    "crop": crop,
                    "available_crops": available[:15]
                }

            if state:
                state_mask = crop_results['State'].str.contains(state, case=False, na=False)
                state_results = crop_results[state_mask].copy()

                if len(state_results) == 0:
                    available_states = sorted(crop_results['State'].dropna().unique().tolist())
                    return {
                        "error": "state_not_found",
                        "crop": crop,
                        "state": state,
                        "available_states": available_states[:15]
                    }

                result = state_results
            else:
                result = crop_results

            if market:
                mkt_mask = result['Market'].str.contains(market, case=False, na=False)
                mkt_results = result[mkt_mask].copy()
                if len(mkt_results) > 0:
                    result = mkt_results

            if 'Arrival Date' not in result.columns:
                result['Arrival Date'] = pd.Timestamp.now()

            result = result.sort_values('Arrival Date', ascending=False)
            latest = result.iloc[0]

            def safe_float(val, default=0):
                try:
                    return float(val) if pd.notna(val) else default
                except:
                    return default

            return {
                "success": True,
                "no_state_specified": state is None,
                "crop": str(latest.get('Commodity', crop)),
                "state": str(latest.get('State', 'Unknown')),
                "market": str(latest.get('Market', 'Unknown')),
                "district": str(latest.get('District', 'Unknown')),
                "date": str(latest['Arrival Date'].date()) if pd.notna(latest['Arrival Date']) else datetime.now().strftime('%Y-%m-%d'),
                "min_price": safe_float(latest.get('Min Price')),
                "max_price": safe_float(latest.get('Max Price')),
                "modal_price": safe_float(latest.get('Modal Price')),
                "arrival_quantity": safe_float(latest.get('Arrival Quantity')),
                "unit": "Rs/quintal"
            }

        except Exception as e:
            return {"error": f"Error processing price data: {str(e)}"}

    def get_price_trend(self, crop, state, days=30):
        try:
            if self.df is None or len(self.df) == 0:
                if not self.load_data():
                    return {"error": "Market data not available"}

            mask = (self.df['Commodity'].str.contains(crop, case=False, na=False)) & \
                   (self.df['State'].str.contains(state, case=False, na=False))
            trend_data = self.df[mask].copy()

            if len(trend_data) == 0:
                return {"error": f"No trend data found for {crop} in {state}"}

            trend_data['Arrival Date'] = pd.to_datetime(trend_data['Arrival Date'], errors='coerce')
            trend_data = trend_data.dropna(subset=['Arrival Date'])
            trend_data = trend_data.sort_values('Arrival Date').tail(days)

            result = []
            for _, row in trend_data.iterrows():
                result.append({
                    "date": row['Arrival Date'].strftime('%Y-%m-%d'),
                    "modal_price": float(row.get('Modal Price', 0)) if pd.notna(row.get('Modal Price')) else 0,
                    "min_price": float(row.get('Min Price', 0)) if pd.notna(row.get('Min Price')) else 0,
                    "max_price": float(row.get('Max Price', 0)) if pd.notna(row.get('Max Price')) else 0,
                    "market": str(row.get('Market', 'Unknown'))
                })

            if result:
                prices = [r['modal_price'] for r in result if r['modal_price'] > 0]
                if prices:
                    return {
                        "data": result,
                        "summary": {
                            "average_price": sum(prices) / len(prices),
                            "highest_price": max(prices),
                            "lowest_price": min(prices),
                            "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                            "trend": "up" if len(prices) > 1 and prices[-1] > prices[0] else "down" if len(prices) > 1 else "stable"
                        }
                    }
            return result
        except Exception as e:
            return {"error": f"Error processing trend data: {str(e)}"}

    def generate_report(self):
        try:
            if self.df is None or len(self.df) == 0:
                if not self.load_data():
                    return {"error": "Market data not available"}

            report = {
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_records": len(self.df),
                "crops": int(self.df['Commodity'].nunique()),
                "states": int(self.df['State'].nunique()) if 'State' in self.df.columns else 0,
                "markets": int(self.df['Market'].nunique()) if 'Market' in self.df.columns else 0,
            }

            if 'Arrival Date' in self.df.columns:
                valid_dates = self.df['Arrival Date'].dropna()
                if len(valid_dates) > 0:
                    report['date_range'] = {
                        "from": valid_dates.min().strftime('%Y-%m-%d'),
                        "to": valid_dates.max().strftime('%Y-%m-%d')
                    }

            if 'Modal Price' in self.df.columns:
                avg_prices = self.df.groupby('Commodity')['Modal Price'].mean().sort_values(ascending=False)
                report['avg_price_by_crop'] = {k: float(v) for k, v in avg_prices.head(10).items() if pd.notna(v)}

            if 'Market' in self.df.columns:
                top_markets = self.df['Market'].value_counts().head(10)
                report['top_markets'] = {k: int(v) for k, v in top_markets.items()}

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
        try:
            if self.df is None or len(self.df) == 0:
                return []
            crops = self.df['Commodity'].dropna().unique()
            return sorted([str(c) for c in crops])[:limit]
        except:
            return []

    def get_available_states(self, crop=None):
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
        try:
            if self.df is None or len(self.df) == 0:
                return {"error": "Data not available"}
            mask = (self.df['Modal Price'] >= min_price) & (self.df['Modal Price'] <= max_price)
            if state:
                mask &= self.df['State'].str.contains(state, case=False, na=False)
            results = self.df[mask].copy().sort_values('Modal Price')
            return results[['Commodity', 'State', 'Market', 'Modal Price']].drop_duplicates().head(20).to_dict('records')
        except Exception as e:
            return {"error": str(e)}