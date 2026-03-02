import os
import numpy as np
import tensorflow as tf
from keras import layers, models
from keras.applications import MobileNetV2
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
import pickle

class PlantDiseaseTrainer:
    def __init__(self):
        self.data_dir = "data/plant_disease/plantvillage dataset/color"
        self.model_path = "models/disease_model.h5"
        self.class_indices_path = "models/class_indices.pkl"
        self.img_size = (224, 224)
        self.batch_size = 32
        self.epochs = 20
        
    def prepare_data(self):
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            validation_split=0.2
        )
        
        val_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=0.2
        )
        
        self.train_generator = train_datagen.flow_from_directory(
            self.data_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            subset='training',
            shuffle=True,
            verbose=0
        )
        
        self.val_generator = val_datagen.flow_from_directory(
            self.data_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            subset='validation',
            shuffle=False,
            verbose=0
        )
        
        with open(self.class_indices_path, 'wb') as f:
            pickle.dump(self.train_generator.class_indices, f)
        
        return self.train_generator, self.val_generator
    
    def build_model(self):
        num_classes = len(self.train_generator.class_indices)
        
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.img_size, 3)
        )
        
        base_model.trainable = False
        
        self.model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return self.model
    
    def train(self):
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            ),
            ModelCheckpoint(
                filepath=self.model_path,
                monitor='val_accuracy',
                save_best_only=True,
                verbose=0
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.2,
                patience=3,
                min_lr=0.00001
            )
        ]
        
        history = self.model.fit(
            self.train_generator,
            validation_data=self.val_generator,
            epochs=self.epochs,
            callbacks=callbacks,
            verbose=0
        )
        
        self.model.save(self.model_path)
        
        return history