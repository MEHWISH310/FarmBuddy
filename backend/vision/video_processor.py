import cv2
import os
import numpy as np
from datetime import datetime
from .frame_extractor import FrameExtractor
from .predict_disease import DiseasePredictor

class VideoProcessor:
    def __init__(self):
        self.frame_extractor = FrameExtractor()
        self.disease_predictor = DiseasePredictor()
        self.output_dir = "uploads/processed_videos"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_video(self, video_path, frame_interval=30, analyze_frames=True):
        results = {
            'video': os.path.basename(video_path),
            'frames_analyzed': 0,
            'disease_detections': [],
            'analysis': {}
        }
        
        if not os.path.exists(video_path):
            results['error'] = 'Video file not found'
            return results
        
        frames = self.frame_extractor.extract_frames(video_path, frame_interval)
        results['total_frames'] = len(frames)
        
        if analyze_frames and frames:
            disease_counts = {}
            
            for frame in frames[:10]:
                try:
                    prediction = self.disease_predictor.predict(frame['path'])
                    
                    if prediction:
                        disease_name = prediction.get('disease', 'unknown')
                        disease_counts[disease_name] = disease_counts.get(disease_name, 0) + 1
                        
                        results['disease_detections'].append({
                            'frame': frame['filename'],
                            'timestamp': frame.get('timestamp', 0),
                            'disease': disease_name,
                            'confidence': prediction.get('confidence', 0)
                        })
                except:
                    continue
            
            if disease_counts:
                primary_disease = max(disease_counts, key=disease_counts.get)
                results['analysis']['primary_disease'] = primary_disease
                results['analysis']['disease_distribution'] = disease_counts
                results['analysis']['total_detections'] = sum(disease_counts.values())
        
        return results
    
    def analyze_plant_health(self, video_path):
        results = self.process_video(video_path, frame_interval=60)
        
        if 'analysis' in results:
            health_status = 'Healthy'
            if results['analysis'].get('primary_disease'):
                if any(word in results['analysis']['primary_disease'].lower() 
                      for word in ['blight', 'rot', 'spot', 'mildew']):
                    health_status = 'Unhealthy - Disease Detected'
            
            results['analysis']['health_status'] = health_status
        
        return results
    
    def generate_report(self, video_path):
        results = self.analyze_plant_health(video_path)
        
        report_path = os.path.join(
            self.output_dir, 
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        with open(report_path, 'w') as f:
            f.write(f"Video Analysis Report\n")
            f.write(f"====================\n")
            f.write(f"Video: {results.get('video', 'Unknown')}\n")
            f.write(f"Frames Analyzed: {results.get('frames_analyzed', 0)}\n")
            f.write(f"Health Status: {results.get('analysis', {}).get('health_status', 'Unknown')}\n")
            
            if results.get('disease_detections'):
                f.write(f"\nDisease Detections:\n")
                for det in results['disease_detections'][:5]:
                    f.write(f"  - {det['disease']} (confidence: {det.get('confidence', 0):.2f})\n")
        
        return results, report_path
    
    def extract_and_save_frames(self, video_path, output_folder=None):
        if output_folder is None:
            output_folder = os.path.join(self.output_dir, 'extracted_frames')
        
        os.makedirs(output_folder, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        frames_saved = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 30 == 0:
                filename = f"frame_{frame_count:06d}.jpg"
                filepath = os.path.join(output_folder, filename)
                cv2.imwrite(filepath, frame)
                frames_saved.append(filepath)
            
            frame_count += 1
        
        cap.release()
        return frames_saved