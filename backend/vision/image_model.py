import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2, ResNet50, VGG16
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

class ImageModelBuilder:
    def __init__(self, input_size=(224, 224, 3), num_classes=10):
        self.input_size = input_size
        self.num_classes = num_classes
        self.model = None
        
    def build_mobilenet(self, weights='imagenet', trainable=False):
        base_model = MobileNetV2(
            weights=weights,
            include_top=False,
            input_shape=self.input_size
        )
        
        base_model.trainable = trainable
        
        self.model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return self.model
    
    def build_resnet(self, weights='imagenet', trainable=False):
        base_model = ResNet50(
            weights=weights,
            include_top=False,
            input_shape=self.input_size
        )
        
        base_model.trainable = trainable
        
        self.model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return self.model
    
    def build_vgg(self, weights='imagenet', trainable=False):
        base_model = VGG16(
            weights=weights,
            include_top=False,
            input_shape=self.input_size
        )
        
        base_model.trainable = trainable
        
        self.model = models.Sequential([
            base_model,
            layers.Flatten(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return self.model
    
    def build_cnn(self):
        self.model = models.Sequential([
            layers.Conv2D(32, (3, 3), activation='relu', input_shape=self.input_size),
            layers.MaxPooling2D((2, 2)),
            
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            
            layers.Conv2D(128, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            
            layers.Flatten(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return self.model
    
    def compile_model(self, learning_rate=0.001):
        if self.model:
            self.model.compile(
                optimizer=Adam(learning_rate=learning_rate),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
        return self.model
    
    def get_callbacks(self, model_path='best_model.h5'):
        return [
            EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
            ModelCheckpoint(model_path, monitor='val_accuracy', save_best_only=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.00001)
        ]
    
    def create_data_generators(self, train_dir, val_dir, img_size=(224, 224), batch_size=32):
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True
        )
        
        val_datagen = ImageDataGenerator(rescale=1./255)
        
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=img_size,
            batch_size=batch_size,
            class_mode='categorical'
        )
        
        val_generator = val_datagen.flow_from_directory(
            val_dir,
            target_size=img_size,
            batch_size=batch_size,
            class_mode='categorical'
        )
        
        return train_generator, val_generator
    
    def save_model(self, path):
        if self.model:
            self.model.save(path)
            return True
        return False
    
    def load_model(self, path):
        if os.path.exists(path):
            self.model = tf.keras.models.load_model(path)
            return True
        return False