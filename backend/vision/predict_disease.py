import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import pickle

class DiseasePredictor:
    def __init__(self):
        self.model_path = "models/disease_model.h5"
        self.class_indices_path = "models/class_indices.pkl"
        self.model = None
        self.class_names = None
        self.load_model()
        
    def load_model(self):
        """Load trained model and class indices"""
        print("Loading model...")
        self.model = tf.keras.models.load_model(self.model_path)
        
        with open(self.class_indices_path, 'rb') as f:
            class_indices = pickle.load(f)
        
        self.class_names = {v: k for k, v in class_indices.items()}
        print(f"✅ Model loaded. {len(self.class_names)} classes")
        
    def preprocess_image(self, img_path):
        """Preprocess image for prediction"""
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        return img_array
    
    def predict(self, img_path):
        """Predict disease for image"""
        if self.model is None:
            self.load_model()
        
        img_array = self.preprocess_image(img_path)
        predictions = self.model.predict(img_array)
        predicted_class = np.argmax(predictions[0])
        confidence = np.max(predictions[0])
        
        disease_name = self.class_names[predicted_class]
        treatment = self.get_treatment_advice(disease_name)
        
        return {
            'disease': disease_name,
            'confidence': float(confidence),
            'treatment': treatment
        }
    
    def get_treatment_advice(self, disease_name):
        """Get treatment advice based on disease"""
        
        if '___' in disease_name:
            parts = disease_name.split('___')
            crop = parts[0]
            disease = parts[1].replace('_', ' ')
        else:
            crop = "Unknown"
            disease = disease_name
        
        treatments = {
            'Apple_scab': 'Apply fungicides containing copper oxychloride. Remove infected leaves.',
            'Black_rot': 'Prune infected branches. Apply copper-based fungicides.',
            'Cedar_apple_rust': 'Remove cedar trees nearby. Apply fungicides in spring.',
            'Common_rust': 'Use rust-resistant varieties. Apply sulfur-based fungicides.',
            'Late_blight': 'Apply fungicides with mancozeb or chlorothalonil. Destroy infected plants.',
            'Early_blight': 'Rotate crops. Apply fungicides with azoxystrobin.',
            'Bacterial_spot': 'Use copper-based bactericides. Remove infected leaves.',
            'Powdery_mildew': 'Apply sulfur or potassium bicarbonate. Ensure good air circulation.',
            'healthy': 'Your plant looks healthy! Continue good practices.'
        }
        
        for key in treatments:
            if key.lower() in disease.lower():
                return treatments[key]
        
        return f"Consult local agriculture officer for {disease} treatment in {crop}."