import os
import numpy as np
import tensorflow as tf
from PIL import Image as PILImage, ImageEnhance
import pickle
import logging
from collections import Counter

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

    # ── File finder ───────────────────────────────────────────────────────────
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
        parts   = raw_key.split('___')
        plant   = parts[0].replace('_', ' ').strip().title()
        disease = parts[1].replace('_', ' ').strip().title() if len(parts) > 1 else ''
        return f"{plant} - {disease}" if disease else plant

    @staticmethod
    def _to_lookup_key(raw_key):
        return raw_key.replace('___', ' ').replace('_', ' ').lower().strip()

    # ── Model loading ─────────────────────────────────────────────────────────
    def _load(self):
        try:
            model_path   = self.find_file(self.model_paths,         'model file')
            indices_path = self.find_file(self.class_indices_paths, 'class indices file')

            if not model_path or not indices_path:
                raise FileNotFoundError('Model files not found')

            with open(indices_path, 'rb') as f:
                class_indices = pickle.load(f)

            self.class_names  = {v: k                       for k, v in class_indices.items()}
            self.class_labels = {v: self._format_label(k)  for k, v in class_indices.items()}

            self.model = self._load_model(model_path, len(class_indices))

            if self.model is None:
                logger.error('All load strategies failed')
                self.model = self._rebuild_model(len(class_indices))
                logger.warning('Using rebuilt model with random weights')
            else:
                logger.info(f'Model ready with {len(class_indices)} classes')

        except Exception as e:
            logger.error(f'Init failed: {e}')
            self.model        = None
            self.class_names  = {0: 'Unknown'}
            self.class_labels = {0: 'Unknown'}

    def _load_model(self, model_path, num_classes):
        try:
            logger.info('Strategy 1: compile=False')
            m = tf.keras.models.load_model(model_path, compile=False)
            logger.info('Strategy 1 SUCCESS')
            return m
        except Exception as e:
            logger.warning(f'Strategy 1 failed: {e}')

        try:
            logger.info('Strategy 2: default')
            m = tf.keras.models.load_model(model_path)
            logger.info('Strategy 2 SUCCESS')
            return m
        except Exception as e:
            logger.warning(f'Strategy 2 failed: {e}')

        try:
            logger.info('Strategy 3: custom_objects InputLayer fix')
            from tensorflow.keras.layers import InputLayer
            class CompatInputLayer(InputLayer):
                def __init__(self, *args, **kwargs):
                    kwargs.pop('batch_shape', None)
                    kwargs.pop('optional', None)
                    super().__init__(*args, **kwargs)
            m = tf.keras.models.load_model(
                model_path, compile=False,
                custom_objects={'InputLayer': CompatInputLayer}
            )
            logger.info('Strategy 3 SUCCESS')
            return m
        except Exception as e:
            logger.warning(f'Strategy 3 failed: {e}')

        try:
            logger.info('Strategy 4: weights-only')
            import h5py
            model = self._rebuild_model(num_classes)
            model.load_weights(model_path, by_name=True, skip_mismatch=True)
            logger.info('Strategy 4 SUCCESS')
            return model
        except Exception as e:
            logger.warning(f'Strategy 4 failed: {e}')

        return None

    def _rebuild_model(self, num_classes):
        from tensorflow.keras import layers, models
        from tensorflow.keras.applications import MobileNetV2
        base = MobileNetV2(weights='imagenet', include_top=False,
                           input_shape=(224, 224, 3))
        base.trainable = False
        m = models.Sequential([
            base,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(num_classes, activation='softmax')
        ])
        m.compile(optimizer='adam', loss='categorical_crossentropy',
                  metrics=['accuracy'])
        return m

    # ── Preprocessing ─────────────────────────────────────────────────────────
    def _pil_to_array(self, pil_img):
        """Resize PIL image to 224x224 and normalise to [0,1]."""
        pil_img = pil_img.resize((224, 224), PILImage.LANCZOS)
        return np.array(pil_img, dtype=np.float32) / 255.0

    def preprocess_image(self, img_path):
        """Single-image preprocessing — used by the image endpoint."""
        if not os.path.exists(img_path):
            raise FileNotFoundError(f'Image not found: {img_path}')
        pil_img = PILImage.open(img_path).convert('RGB')
        arr = self._pil_to_array(pil_img)
        return np.expand_dims(arr, axis=0)   # (1, 224, 224, 3)

    def _tta_batch(self, img_path):
        """
        Test-Time Augmentation — return a batch of 5 variants of the frame.
        Averaging predictions over these variants reduces noise significantly.
        """
        pil_img = PILImage.open(img_path).convert('RGB')
        w, h    = pil_img.size

        # Centre-crop coordinates (80 % of frame)
        cw, ch = int(w * 0.80), int(h * 0.80)
        l,  t  = (w - cw) // 2, (h - ch) // 2
        center_crop = pil_img.crop((l, t, l + cw, t + ch))

        variants = [
            center_crop,                                                    # 1. centre crop
            pil_img,                                                        # 2. full frame
            pil_img.crop((l, 0, l + cw, ch)),                              # 3. top crop
            center_crop.transpose(PILImage.FLIP_LEFT_RIGHT),               # 4. h-flip
            ImageEnhance.Brightness(center_crop).enhance(1.15),            # 5. brighter
        ]

        return np.stack([self._pil_to_array(v) for v in variants], axis=0)  # (5,224,224,3)

    # ── Single image predict ──────────────────────────────────────────────────
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

            display_name = self.class_labels.get(predicted_class, f'Class_{predicted_class}')
            raw_key      = self.class_names.get(predicted_class, 'unknown')
            lookup_key   = self._to_lookup_key(raw_key)
            treatment    = self.get_treatment(lookup_key, display_name)

            logger.info(f'Predicted: {display_name} ({confidence*100:.2f}%)')
            return {'disease': display_name, 'confidence': confidence,
                    'treatment': treatment, 'success': True}

        except Exception as e:
            logger.error(f'Prediction error: {e}')
            return {'disease': 'error', 'confidence': 0.0,
                    'treatment': f'Error: {e}', 'error': str(e)}

    # ── Video predict ─────────────────────────────────────────────────────────
    def predict_from_video(self, video_path, frame_extractor=None):
        """
        High-accuracy video prediction using:
          1. 20 evenly-spaced key frames
          2. Test-Time Augmentation (5 variants per frame = 100 predictions)
          3. Confidence² weighted voting — high-confidence frames dominate
          4. Low-confidence predictions (<40%) discarded as noise
        """
        try:
            if self.model is None:
                self._load()
            if self.model is None:
                return {'disease': 'unknown', 'confidence': 0.0,
                        'treatment': 'Model not available.',
                        'error': 'Model not loaded', 'success': False}

            if frame_extractor is None:
                from vision.frame_extractor import FrameExtractor
                frame_extractor = FrameExtractor()

            logger.info(f'Extracting frames from: {video_path}')
            frames = frame_extractor.extract_key_frames(video_path, num_frames=20)

            if not frames:
                return {'disease': 'unknown', 'confidence': 0.0,
                        'treatment': 'Could not extract frames from video.',
                        'error': 'No frames extracted', 'success': False}

            logger.info(f'Running TTA on {len(frames)} frames (5 variants each)…')

            frame_predictions = []
            extracted_paths   = []

            for frame in frames:
                frame_path = frame['path']
                extracted_paths.append(frame_path)

                try:
                    # TTA: run 5 variants through the model in one batch call
                    batch      = self._tta_batch(frame_path)        # (5,224,224,3)
                    preds      = self.model.predict(batch, verbose=0)  # (5, num_classes)
                    avg_preds  = np.mean(preds, axis=0)             # average over variants
                    pred_class = int(np.argmax(avg_preds))
                    confidence = float(np.max(avg_preds))

                    display_name = self.class_labels.get(pred_class, f'Class_{pred_class}')
                    raw_key      = self.class_names.get(pred_class, 'unknown')
                    lookup_key   = self._to_lookup_key(raw_key)
                    treatment    = self.get_treatment(lookup_key, display_name)

                    frame_predictions.append({
                        'frame_number': frame.get('frame_number', 0),
                        'disease':      display_name,
                        'confidence':   confidence,
                        'treatment':    treatment,
                    })
                    logger.info(f'  Frame {frame.get("frame_number",0)}: '
                                f'{display_name} ({confidence*100:.1f}%)')

                except Exception as fe:
                    logger.warning(f'  Frame error: {fe}')

            # Clean up frame files
            for path in extracted_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

            if not frame_predictions:
                return {'disease': 'unknown', 'confidence': 0.0,
                        'treatment': 'Could not analyse any frames.',
                        'error': 'All frame predictions failed', 'success': False}

            # ── Aggregation ───────────────────────────────────────────────────
            # Step 1: drop low-confidence noise (< 40%)
            THRESHOLD    = 0.40
            strong_preds = [fp for fp in frame_predictions
                            if fp['confidence'] >= THRESHOLD]
            working      = strong_preds if len(strong_preds) >= 3 else frame_predictions

            # Step 2: confidence² weighted scoring
            disease_scores = {}
            disease_counts = Counter()
            for fp in working:
                d = fp['disease']
                disease_counts[d] += 1
                disease_scores[d]  = disease_scores.get(d, 0.0) + fp['confidence'] ** 2

            # Step 3: pick winner
            top_disease    = max(disease_scores, key=disease_scores.get)
            top_confs      = [fp['confidence'] for fp in frame_predictions
                              if fp['disease'] == top_disease]
            avg_confidence = float(np.mean(top_confs))

            # Retrieve treatment
            raw_key = None
            for k, v in self.class_labels.items():
                if v == top_disease:
                    raw_key = self.class_names.get(k)
                    break
            lookup_key = self._to_lookup_key(raw_key) if raw_key else top_disease.lower()
            treatment  = self.get_treatment(lookup_key, top_disease)

            # Summary string
            unique_diseases = disease_counts.most_common(3)
            total           = len(working)
            video_summary   = ', '.join(
                f"{d} ({c}/{total} frames)" for d, c in unique_diseases
            )

            logger.info(
                f'Final: {top_disease} | avg conf {avg_confidence*100:.1f}% | '
                f'{disease_counts[top_disease]}/{total} frames'
            )

            return {
                'disease':         top_disease,
                'confidence':      avg_confidence,
                'treatment':       treatment,
                'success':         True,
                'frame_count':     len(frame_predictions),
                'all_predictions': frame_predictions,
                'video_summary':   video_summary,
            }

        except Exception as e:
            logger.error(f'Video prediction error: {e}')
            import traceback; traceback.print_exc()
            return {'disease': 'error', 'confidence': 0.0,
                    'treatment': f'Error: {e}',
                    'error': str(e), 'success': False}

    # ── Treatment database ────────────────────────────────────────────────────
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

        return (f'Disease detected: {display_name}. '
                f'(1) Remove infected plant material. '
                f'(2) Apply appropriate fungicide or bactericide. '
                f'(3) Improve air circulation and avoid overhead watering. '
                f'(4) Consult your local agricultural extension officer.')


if __name__ == '__main__':
    predictor = DiseasePredictor()
    print('Model loaded:', predictor.model is not None)
    print('Classes:', len(predictor.class_names) if predictor.class_names else 0)