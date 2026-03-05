import os
import numpy as np
import tensorflow as tf
from keras.preprocessing import image
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiseasePredictor:
    def __init__(self):
        self.current_dir    = os.path.dirname(os.path.abspath(__file__))
        self.project_root   = os.path.dirname(self.current_dir)
        self.farmbuddy_root = os.path.dirname(self.project_root)

        self.model_paths = [
            os.path.join(self.project_root,   'models', 'disease_model.h5'),
            os.path.join(self.farmbuddy_root, 'models', 'disease_model.h5'),
            os.path.join(self.current_dir,    'models', 'disease_model.h5'),
        ]
        self.class_indices_paths = [
            os.path.join(self.project_root,   'models', 'class_indices.pkl'),
            os.path.join(self.farmbuddy_root, 'models', 'class_indices.pkl'),
            os.path.join(self.current_dir,    'models', 'class_indices.pkl'),
        ]

        self.model        = None
        self.class_names  = None
        self.class_labels = None
        self._load()

    def find_file(self, paths, description):
        for path in paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                logger.info(f"Found {description} at: {abs_path}")
                return abs_path
        logger.error(f"{description} not found in: {paths}")
        return None

    @staticmethod
    def _format_label(raw_key):
        parts = raw_key.split('___')
        plant   = parts[0].replace('_', ' ').strip().title()
        disease = parts[1].replace('_', ' ').strip().title() if len(parts) > 1 else ''
        return f"{plant} - {disease}" if disease else plant

    @staticmethod
    def _to_lookup_key(raw_key):
        return raw_key.replace('___', ' ').replace('_', ' ').lower().strip()

    def _load(self):
        try:
            model_path   = self.find_file(self.model_paths,         "model file")
            indices_path = self.find_file(self.class_indices_paths, "class indices file")

            if not model_path or not indices_path:
                raise FileNotFoundError("Model files not found")

            with open(indices_path, 'rb') as f:
                class_indices = pickle.load(f)

            self.class_names  = {v: k                      for k, v in class_indices.items()}
            self.class_labels = {v: self._format_label(k) for k, v in class_indices.items()}

            self.model = self._load_model(model_path, len(class_indices))

            if self.model is None:
                logger.error("All load strategies failed")
                self.model = self._rebuild_model(len(class_indices))
                logger.warning("Using rebuilt model with random weights - predictions unreliable")
            else:
                logger.info(f"Model ready with {len(class_indices)} classes")

        except Exception as e:
            logger.error(f"Init failed: {e}")
            self.model        = None
            self.class_names  = {0: "Unknown"}
            self.class_labels = {0: "Unknown"}

    def _load_model(self, model_path, num_classes):
        # Strategy 1: compile=False (handles compiled metrics warning)
        try:
            logger.info("Strategy 1: compile=False")
            m = tf.keras.models.load_model(model_path, compile=False)
            logger.info("Strategy 1 SUCCESS")
            return m
        except Exception as e:
            logger.warning(f"Strategy 1 failed: {e}")

        # Strategy 2: default
        try:
            logger.info("Strategy 2: default")
            m = tf.keras.models.load_model(model_path)
            logger.info("Strategy 2 SUCCESS")
            return m
        except Exception as e:
            logger.warning(f"Strategy 2 failed: {e}")

        # Strategy 3: custom_objects to fix InputLayer Keras version mismatch
        try:
            logger.info("Strategy 3: custom_objects InputLayer fix")
            from tensorflow.keras.layers import InputLayer

            class CompatInputLayer(InputLayer):
                def __init__(self, *args, **kwargs):
                    kwargs.pop('batch_shape', None)
                    kwargs.pop('optional', None)
                    super().__init__(*args, **kwargs)

            m = tf.keras.models.load_model(
                model_path,
                compile=False,
                custom_objects={'InputLayer': CompatInputLayer}
            )
            logger.info("Strategy 3 SUCCESS")
            return m
        except Exception as e:
            logger.warning(f"Strategy 3 failed: {e}")

        # Strategy 4: h5py - load weights only into rebuilt architecture
        try:
            logger.info("Strategy 4: h5py weights-only into rebuilt architecture")
            import h5py
            model = self._rebuild_model(num_classes)
            with h5py.File(model_path, 'r') as f:
                model.load_weights(model_path, by_name=False, skip_mismatch=True)
            logger.info("Strategy 4 SUCCESS")
            return model
        except Exception as e:
            logger.warning(f"Strategy 4 failed: {e}")

        return None

    def _rebuild_model(self, num_classes):
        from tensorflow.keras import layers, models
        m = models.Sequential([
            layers.Input(shape=(224, 224, 3)),
            layers.Conv2D(32,  (3,3), activation='relu', padding='same'),
            layers.MaxPooling2D((2,2)),
            layers.Conv2D(64,  (3,3), activation='relu', padding='same'),
            layers.MaxPooling2D((2,2)),
            layers.Conv2D(128, (3,3), activation='relu', padding='same'),
            layers.MaxPooling2D((2,2)),
            layers.Conv2D(256, (3,3), activation='relu', padding='same'),
            layers.MaxPooling2D((2,2)),
            layers.Flatten(),
            layers.Dense(512, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation='softmax')
        ])
        m.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return m

    def preprocess_image(self, img_path):
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image not found: {img_path}")
        img = image.load_img(img_path, target_size=(224, 224))
        arr = image.img_to_array(img)
        arr = np.expand_dims(arr, axis=0) / 255.0
        return arr

    def predict(self, img_path):
        try:
            if self.model is None:
                self._load()
            if self.model is None:
                return {'disease': 'unknown', 'confidence': 0.0,
                        'treatment': 'Model not available.', 'error': 'Model not loaded'}

            arr             = self.preprocess_image(img_path)
            preds           = self.model.predict(arr, verbose=0)
            predicted_class = int(np.argmax(preds[0]))
            confidence      = float(np.max(preds[0]))

            display_name = self.class_labels.get(predicted_class, f"Class_{predicted_class}")
            raw_key      = self.class_names.get(predicted_class, "unknown")
            lookup_key   = self._to_lookup_key(raw_key)
            treatment    = self.get_treatment(lookup_key, display_name)

            logger.info(f"Predicted: {display_name} ({confidence*100:.2f}%)")
            return {'disease': display_name, 'confidence': confidence,
                    'treatment': treatment, 'success': True}

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'disease': 'error', 'confidence': 0.0,
                    'treatment': f'Error: {e}', 'error': str(e)}

    def get_treatment(self, lookup_key, display_name):
        treatments = {
            'apple apple scab': 'Apply fungicides containing copper oxychloride or myclobutanil. Remove infected leaves. Ensure good air circulation.',
            'apple black rot': 'Prune infected branches 6-8 inches below visible damage. Apply copper-based fungicides in spring. Remove mummified fruits.',
            'apple cedar apple rust': 'Remove nearby cedar trees if possible. Apply fungicides with myclobutanil or sulfur. Plant resistant varieties.',
            'apple healthy': 'Your apple plant looks healthy! Continue regular maintenance and monitoring.',
            'blueberry healthy': 'Your blueberry plant is healthy! Maintain proper soil pH (4.5-5.5) and consistent moisture.',
            'cherry (including sour) powdery mildew': 'Apply sulfur or potassium bicarbonate sprays. Improve air circulation. Avoid overhead irrigation.',
            'cherry (including sour) healthy': 'Your cherry tree is healthy! Continue proper pruning and fertilization.',
            'corn (maize) cercospora leaf spot gray leaf spot': 'Rotate crops annually. Apply fungicides with azoxystrobin. Plant resistant hybrids.',
            'corn (maize) common rust': 'Use rust-resistant varieties. Apply sulfur-based fungicides early. Ensure proper plant spacing.',
            'corn (maize) northern leaf blight': 'Rotate crops annually. Apply fungicides with azoxystrobin. Plant resistant hybrids.',
            'corn (maize) healthy': 'Your corn plant is healthy! Maintain good irrigation and fertilization.',
            'grape black rot': 'Apply fungicides with myclobutanil or copper. Remove infected berries and leaves. Ensure good vine spacing.',
            'grape esca (black measles)': 'Prune infected vines back to healthy wood. No curative chemical control. Maintain vine health.',
            'grape leaf blight (isariopsis leaf spot)': 'Apply copper-based fungicides. Remove infected leaves. Improve air circulation.',
            'grape healthy': 'Your grape vine is healthy! Continue proper trellising and pruning.',
            'orange haunglongbing (citrus greening)': 'No cure available. Remove infected trees. Control Asian citrus psyllid with insecticides.',
            'peach bacterial spot': 'Apply copper-based bactericides in spring. Prune for good air circulation. Avoid overhead irrigation.',
            'peach healthy': 'Your peach tree is healthy! Continue proper pruning and fertilization.',
            'pepper, bell bacterial spot': 'Apply copper-based bactericides. Rotate crops. Use disease-free certified seeds.',
            'pepper, bell healthy': 'Your bell pepper plant is healthy! Maintain consistent soil moisture.',
            'potato early blight': 'Apply fungicides with chlorothalonil or azoxystrobin. Rotate crops every 2-3 years. Avoid overhead irrigation.',
            'potato late blight': 'Apply fungicides with mancozeb or metalaxyl immediately. Destroy infected plants. Use disease-free seed potatoes.',
            'potato healthy': 'Your potato plant is healthy! Maintain proper hilling and soil moisture.',
            'raspberry healthy': 'Your raspberry plant is healthy! Ensure proper trellising and annual cane removal.',
            'soybean healthy': 'Your soybean plant is healthy! Monitor for aphids and maintain proper row spacing.',
            'squash powdery mildew': 'Apply sulfur or potassium bicarbonate sprays. Ensure good air circulation. Water at base only.',
            'strawberry leaf scorch': 'Remove and destroy infected leaves. Apply fungicides with myclobutanil. Avoid overhead irrigation.',
            'strawberry healthy': 'Your strawberry plant is healthy! Maintain proper irrigation and mulching.',
            'tomato bacterial spot': 'Use copper-based bactericides. Remove infected leaves. Avoid working with plants when wet.',
            'tomato early blight': 'Apply fungicides with azoxystrobin or chlorothalonil. Mulch around plants. Rotate crops.',
            'tomato late blight': 'Apply fungicides with chlorothalonil or mancozeb. Destroy infected plants immediately.',
            'tomato leaf mold': 'Improve ventilation. Reduce humidity. Apply sulfur-based fungicides.',
            'tomato septoria leaf spot': 'Apply copper-based fungicides. Remove infected leaves. Mulch to prevent soil splash.',
            'tomato spider mites two-spotted spider mite': 'Apply insecticidal soap or neem oil. Increase humidity. Remove infested leaves.',
            'tomato target spot': 'Apply fungicides with azoxystrobin. Rotate crops annually. Avoid overhead irrigation.',
            'tomato tomato yellow leaf curl virus': 'Control whiteflies with insecticidal soap or neem oil. Remove infected plants. Use reflective mulches.',
            'tomato tomato mosaic virus': 'Remove infected plants. Control aphids. Disinfect tools. Use virus-resistant varieties.',
            'tomato healthy': 'Your tomato plant is healthy! Continue regular care and monitoring.',
        }

        if lookup_key in treatments:
            return treatments[lookup_key]

        lookup_words = set(lookup_key.split())
        best_key, best_score = None, 0
        for key in treatments:
            score = len(set(key.split()) & lookup_words)
            if score > best_score:
                best_score, best_key = score, key
        if best_key and best_score >= 2:
            return treatments[best_key]

        if 'healthy' in lookup_key:
            return f'Your {display_name.split(" - ")[0]} plant appears healthy! Continue good agricultural practices.'

        return (f"Disease detected: {display_name}. "
                f"(1) Remove infected plant material. "
                f"(2) Apply appropriate fungicide or bactericide. "
                f"(3) Improve air circulation and avoid overhead watering. "
                f"(4) Consult your local agricultural extension officer.")


if __name__ == "__main__":
    predictor = DiseasePredictor()
    print("Model loaded:" , predictor.model is not None)
    print("Classes:", len(predictor.class_names) if predictor.class_names else 0)