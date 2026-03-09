import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import confusion_matrix

model = load_model("backend/models/disease_model.h5")

with open("backend/models/class_indices.pkl", "rb") as f:
    class_indices = pickle.load(f)

class_names = list(class_indices.keys())

dataset_path = "data/plant_disease/plantvillage dataset/color"

img_size = 224
batch_size = 32

datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2
)

val_data = datagen.flow_from_directory(
    dataset_path,
    target_size=(img_size, img_size),
    batch_size=batch_size,
    class_mode="categorical",
    subset="validation",
    shuffle=False
)

print("Generating predictions...")

predictions = model.predict(val_data)

y_pred = np.argmax(predictions, axis=1)
y_true = val_data.classes

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(20,20))

sns.heatmap(
    cm,
    xticklabels=class_names,
    yticklabels=class_names,
    cmap="Blues",
    linewidths=0.5
)

plt.xlabel("Predicted Class")
plt.ylabel("Actual Class")
plt.title("Plant Disease Classification Confusion Matrix")

plt.xticks(rotation=90)
plt.yticks(rotation=0)

plt.tight_layout()

plt.savefig("backend/models/confusion_matrix_labeled.png", dpi=300)

plt.show()