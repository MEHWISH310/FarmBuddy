import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import pickle
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiseasePredictor:
    def __init__(self):
        # Get the correct paths
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.current_dir)  # backend folder
        self.farmbuddy_root = os.path.dirname(self.project_root)  # FarmBuddy folder
        
        # Update model paths to look in multiple locations
        self.model_paths = [
            os.path.join(self.project_root, 'models', 'disease_model.h5'),  # backend/models/
            os.path.join(self.farmbuddy_root, 'models', 'disease_model.h5'),  # FarmBuddy/models/
            os.path.join(self.current_dir, 'models', 'disease_model.h5'),  # nlp/models/
            'models/disease_model.h5',  # relative path
        ]
        
        self.class_indices_paths = [
            os.path.join(self.project_root, 'models', 'class_indices.pkl'),
            os.path.join(self.farmbuddy_root, 'models', 'class_indices.pkl'),
            os.path.join(self.current_dir, 'models', 'class_indices.pkl'),
            'models/class_indices.pkl',
        ]
        
        self.model = None
        self.class_names = None
        self.load_model()
        
    def find_file(self, paths, description):
        """Find a file from list of possible paths"""
        for path in paths:
            if os.path.exists(path):
                logger.info(f"✅ Found {description} at: {path}")
                return path
        logger.warning(f"⚠️ {description} not found in any of: {paths}")
        return None
        
    def load_model(self):
        """Load the trained model and class indices"""
        try:
            # Find model file
            model_path = self.find_file(self.model_paths, "model file")
            if model_path is None:
                raise FileNotFoundError("Model file not found")
            
            # Find class indices file
            indices_path = self.find_file(self.class_indices_paths, "class indices file")
            if indices_path is None:
                raise FileNotFoundError("Class indices file not found")
            
            # Load class indices first (needed for rebuilding)
            with open(indices_path, 'rb') as f:
                class_indices = pickle.load(f)
            self.class_names = {v: k.replace('_', ' ').title() for k, v in class_indices.items()}
            
            # Try loading model with different strategies
            self.model = self._load_model_with_fallbacks(model_path)
            
            if self.model is None:
                self.model = self._rebuild_model(len(class_indices))
                logger.info("⚠️ Rebuilt model architecture (weights not loaded)")
            else:
                logger.info(f"✅ Model loaded successfully from {model_path}")
                
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            self.model = None
            self.class_names = {0: "Unknown", 1: "Healthy"}  # Fallback
    
    def _load_model_with_fallbacks(self, model_path):
        """Try different loading strategies"""
        try:
            # Strategy 1: Normal load
            logger.info("Attempting to load model normally...")
            return tf.keras.models.load_model(model_path)
        except Exception as e1:
            logger.warning(f"Normal load failed: {e1}")
            
            try:
                # Strategy 2: Load with compile=False
                logger.info("Attempting to load with compile=False...")
                return tf.keras.models.load_model(model_path, compile=False)
            except Exception as e2:
                logger.warning(f"Load with compile=False failed: {e2}")
                
                try:
                    # Strategy 3: Load with safe_mode=False
                    logger.info("Attempting to load with safe_mode=False...")
                    return tf.keras.models.load_model(model_path, safe_mode=False)
                except Exception as e3:
                    logger.warning(f"Load with safe_mode=False failed: {e3}")
                    
                    try:
                        # Strategy 4: Load weights only
                        logger.info("Attempting to load weights only...")
                        model = self._rebuild_model(10)  # Temporary rebuild
                        model.load_weights(model_path)
                        return model
                    except Exception as e4:
                        logger.error(f"All loading strategies failed: {e4}")
                        return None
    
    def _rebuild_model(self, num_classes):
        """Rebuild model architecture"""
        from tensorflow.keras import layers, models
        
        logger.info(f"Rebuilding model with {num_classes} classes...")
        
        model = models.Sequential([
            layers.Input(shape=(224, 224, 3)),
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
            layers.MaxPooling2D((2, 2)),
            layers.Flatten(),
            layers.Dense(512, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("✅ Model architecture rebuilt")
        return model
    
    def preprocess_image(self, img_path):
        """Preprocess image for prediction"""
        try:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image not found: {img_path}")
                
            img = image.load_img(img_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize to [0,1]
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def predict(self, img_path):
        """Predict disease from image"""
        try:
            if self.model is None:
                self.load_model()
                
            if self.model is None:
                return {
                    'disease': 'unknown',
                    'confidence': 0.0,
                    'treatment': 'Disease detection model not available. Please check model files.',
                    'error': 'Model not loaded'
                }
            
            # Preprocess image
            img_array = self.preprocess_image(img_path)
            
            # Make prediction
            predictions = self.model.predict(img_array, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(np.max(predictions[0]))
            
            # Get disease name
            if self.class_names and predicted_class in self.class_names:
                disease_name = self.class_names[predicted_class]
            else:
                disease_name = f"Class_{predicted_class}"
            
            # Get treatment advice
            treatment = self.get_treatment_advice(disease_name)
            
            # Clean up - remove temporary file
            try:
                if os.path.exists(img_path) and 'temp' in img_path:
                    os.remove(img_path)
            except:
                pass
            
            return {
                'disease': disease_name,
                'confidence': confidence,
                'treatment': treatment,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'disease': 'error',
                'confidence': 0.0,
                'treatment': f'Error analyzing image: {str(e)}',
                'error': str(e)
            }
    
    def get_treatment_advice(self, disease_name):
        """Get treatment advice for detected disease"""
        
        # Comprehensive treatment database
        treatments = {
            'apple scab': 'Apply fungicides containing copper oxychloride or myclobutanil. Remove and destroy infected leaves. Ensure good air circulation by pruning.',
            'apple black rot': 'Prune infected branches 6-8 inches below visible damage. Apply copper-based fungicides in spring. Remove mummified fruits.',
            'apple cedar rust': 'Remove nearby cedar trees if possible. Apply fungicides with myclobutanil or sulfur. Plant resistant varieties.',
            'apple healthy': 'Your apple plant looks healthy! Continue regular maintenance and monitoring.',
            
            'corn common rust': 'Use rust-resistant varieties. Apply sulfur-based fungicides. Ensure proper plant spacing for air circulation.',
            'corn northern leaf blight': 'Rotate crops annually. Apply fungicides with azoxystrobin. Plant resistant hybrids.',
            'corn healthy': 'Your corn plant is healthy! Maintain good irrigation and fertilization practices.',
            
            'grape black rot': 'Apply fungicides with myclobutanil or copper. Remove infected berries and leaves. Ensure good vine spacing.',
            'grape esca': 'Prune infected vines. No chemical control available. Maintain vine health through proper nutrition.',
            'grape leaf blight': 'Apply copper-based fungicides. Remove and destroy infected leaves. Improve air circulation.',
            'grape healthy': 'Your grape vine is healthy! Continue proper trellising and pruning practices.',
            
            'potato early blight': 'Apply fungicides with chlorothalonil or azoxystrobin. Rotate crops every 2-3 years. Avoid overhead irrigation.',
            'potato late blight': 'Apply fungicides with mancozeb or metalaxyl. Destroy infected plants immediately. Use disease-free seed potatoes.',
            'potato healthy': 'Your potato plant is healthy! Maintain proper hilling and soil moisture.',
            
            'tomato bacterial spot': 'Use copper-based bactericides. Remove infected leaves. Avoid working with wet plants.',
            'tomato early blight': 'Apply fungicides with azoxystrobin. Mulch around plants to prevent soil splash. Rotate crops.',
            'tomato late blight': 'Apply fungicides with chlorothalonil. Destroy infected plants. Ensure good air circulation.',
            'tomato leaf mold': 'Improve air circulation. Reduce humidity. Apply sulfur-based fungicides.',
            'tomato septoria leaf spot': 'Apply copper-based fungicides. Remove infected leaves. Mulch to prevent soil splash.',
            'tomato spider mites': 'Apply insecticidal soap or neem oil. Increase humidity. Remove severely infested leaves.',
            'tomato target spot': 'Apply fungicides with azoxystrobin. Rotate crops. Avoid overhead irrigation.',
            'tomato yellow leaf curl': 'Control whiteflies with insecticidal soap. Remove infected plants. Use reflective mulches.',
            'tomato mosaic virus': 'Remove infected plants. Control aphids. Disinfect tools. Use virus-resistant varieties.',
            'tomato healthy': 'Your tomato plant is healthy! Continue regular care and monitoring for pests.',
            
            'strawberry healthy': 'Your strawberry plant is healthy! Maintain proper irrigation and mulch.',
            
            'peach bacterial spot': 'Apply copper-based bactericides in spring. Prune for good air circulation. Avoid overhead irrigation.',
            'peach healthy': 'Your peach tree is healthy! Continue proper pruning and fertilization.',
            
            'bell pepper bacterial spot': 'Apply copper-based bactericides. Rotate crops. Use disease-free seeds.',
            'bell pepper healthy': 'Your bell pepper plant is healthy! Maintain consistent soil moisture.',
            
            'squash powdery mildew': 'Apply sulfur or potassium bicarbonate. Ensure good air circulation. Water at base of plants.',
            'healthy': 'Your plant looks healthy! Continue good agricultural practices.',
            'unknown': 'Disease not in database. Please consult local agriculture officer.'
        }
        
        # Normalize disease name for lookup
        disease_lower = disease_name.lower()
        
        # Direct match
        if disease_lower in treatments:
            return treatments[disease_lower]
        
        # Partial match
        for key, advice in treatments.items():
            if key in disease_lower or disease_lower in key:
                return advice
        
        # Generic response
        if 'healthy' in disease_lower:
            return 'Your plant appears healthy! Continue regular monitoring and good agricultural practices.'
        else:
            return f"Disease detected: {disease_name}. Please consult your local agricultural extension officer for specific treatment recommendations."


# Test the predictor
if __name__ == "__main__":
    predictor = DiseasePredictor()
    print("\n" + "="*50)
    print("DISEASE PREDICTOR TEST")
    print("="*50)
    
    # Print model status
    if predictor.model is not None:
        print(f"✅ Model loaded successfully")
        print(f"📊 Number of classes: {len(predictor.class_names)}")
        print(f"🌱 Sample classes: {list(predictor.class_names.values())[:5]}")
    else:
        print("❌ Model not loaded")