import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
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
        """Prepare data generators"""
        
        # Data augmentation for training
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
        
        # Validation data (only rescaling)
        val_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=0.2
        )
        
        # Training generator
        self.train_generator = train_datagen.flow_from_directory(
            self.data_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            subset='training',
            shuffle=True
        )
        
        # Validation generator
        self.val_generator = val_datagen.flow_from_directory(
            self.data_dir,
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            subset='validation',
            shuffle=False
        )
        
        print(f"\n✅ Training samples: {self.train_generator.samples}")
        print(f"✅ Validation samples: {self.val_generator.samples}")
        print(f"✅ Classes: {len(self.train_generator.class_indices)}")
        
        # Save class indices
        with open(self.class_indices_path, 'wb') as f:
            pickle.dump(self.train_generator.class_indices, f)
        
        return self.train_generator, self.val_generator
    
    def build_model(self):
        """Build transfer learning model"""
        
        num_classes = len(self.train_generator.class_indices)
        
        # Load pre-trained MobileNetV2
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(*self.img_size, 3)
        )
        
        # Freeze base model
        base_model.trainable = False
        
        # Build model
        self.model = models.Sequential([
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        # Compile
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print(f"\n✅ Model built with {num_classes} classes")
        self.model.summary()
        
        return self.model
    
    def train(self):
        """Train the model"""
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            ),
            ModelCheckpoint(
                filepath=self.model_path,
                monitor='val_accuracy',
                save_best_only=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.2,
                patience=3,
                min_lr=0.00001
            )
        ]
        
        # Train
        history = self.model.fit(
            self.train_generator,
            validation_data=self.val_generator,
            epochs=self.epochs,
            callbacks=callbacks
        )
        
        # Save final model
        self.model.save(self.model_path)
        print(f"\n✅ Model saved to {self.model_path}")
        
        return history
    
    def plot_training(self, history):
        """Plot training history"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Accuracy
        ax1.plot(history.history['accuracy'], label='Train Accuracy')
        ax1.plot(history.history['val_accuracy'], label='Val Accuracy')
        ax1.set_title('Model Accuracy')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Accuracy')
        ax1.legend()
        
        # Loss
        ax2.plot(history.history['loss'], label='Train Loss')
        ax2.plot(history.history['val_loss'], label='Val Loss')
        ax2.set_title('Model Loss')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Loss')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('models/training_history.png')
        plt.show()
        
        print("✅ Training plot saved to models/training_history.png")

if __name__ == "__main__":
    # Initialize trainer
    trainer = PlantDiseaseTrainer()
    
    # Prepare data
    print("📊 Preparing data...")
    train_gen, val_gen = trainer.prepare_data()
    
    # Build model
    print("\n🏗️ Building model...")
    model = trainer.build_model()
    
    # Train
    print("\n🎯 Starting training...")
    history = trainer.train()
    
    # Plot results
    trainer.plot_training(history)
    
    print("\n🎉 Training complete!")