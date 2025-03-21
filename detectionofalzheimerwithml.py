# -*- coding: utf-8 -*-
"""DETECTIONofALZHEIMERwithML.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zMTZasJz9FDYznZqDSQd3IPIFNyidD8p
"""

!pip install datasets

!pip install datasets transformers pillow requests imblearn pydot graphviz

import os
import io
import random
import cv2
import requests
import keras
import pandas as pd
import numpy as np
import tensorflow as tf
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.utils import shuffle
from PIL import Image
from io import BytesIO
from datasets import load_dataset
from sklearn.model_selection import train_test_split
from torch.utils.data import random_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import img_to_array
from keras.callbacks import EarlyStopping,ModelCheckpoint
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from tqdm import tqdm
from imblearn.over_sampling import SMOTE

@dataset {alzheimer_mri_dataset,
  author = {Falah.G.Salieh},
  title = {Alzheimer MRI Dataset},
  year = {2023},
  publisher = {Hugging Face},
  version = {1.0},
  url = {https://huggingface.co/datasets/Falah/Alzheimer_MRI}
}

dataset = load_dataset("Falah/Alzheimer_MRI")

print(dataset)

train_dataset = dataset['train']

# Get the total number of samples in the train dataset
total_samples = len(train_dataset)

# Randomly select 3000 samples from the dataset
random_indices = np.random.choice(total_samples, 3500, replace=False)

# Extract the corresponding samples, convert to regular int for indexing
selected_data = [train_dataset[int(i)] for i in random_indices]

# Verify the number of selected samples
print(f"Total selected samples: {len(selected_data)}")

# Create a DataFrame from selected data
image_data = []
labels = []

for sample in selected_data:
    image_data.append(sample['image'])
    labels.append(sample['label'])

# Create a DataFrame with 'image' and 'label' columns
df = pd.DataFrame({
    'image': image_data,
    'label': labels
})

# Shuffle the DataFrame rows
df = shuffle(df, random_state=1000)

# Verify the structure of the DataFrame
print(df.head())

# Optionally display the first image from the DataFrame
first_image = df.iloc[0]['image']
first_label = df.iloc[0]['label']

# Check if the image is already a PIL Image object
if isinstance(first_image, Image.Image):
    plt.imshow(first_image)  # Directly display the PIL image
    plt.title(f"Label: {first_label}")
    plt.axis('off')  # Hide axes
    plt.show()
else:
    print("The image data is not in PIL format.")

def preprocess_images(example):
    example['image'] = example['image'].resize((224, 224))  # Example: Resize image
    return example

# Apply the transformation to the train split
dataset['train'] = dataset['train'].map(preprocess_images)

print(f"Data type of image column: {type(df.iloc[0]['image'])}")

plt.figure(figsize=(50, 50))

for n, i in enumerate(np.random.randint(0, len(df), 50)):
    plt.subplot(10, 5, n + 1)

    # Get the image data from the 'image' column
    image_data = df['image'][i]

    # Check if the image data is a PIL image, and resize it
    if isinstance(image_data, Image.Image):
        img = image_data.resize((224, 224))  # Resize the image
        img = np.array(img)  # Convert PIL image to numpy array for displaying
    else:
        # If the image is not a PIL image, handle accordingly
        img = cv2.resize(image_data, (224, 224))  # Resize if it's a numpy array
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB if using OpenCV

    # Display the image
    plt.imshow(img)
    plt.axis('off')  # Hide axes
    plt.title(df['label'][i], fontsize=25)  # Display the label
plt.show()

# Assuming df contains 'image' (PIL image objects) and 'label' columns
le = LabelEncoder()
df['label'] = le.fit_transform(df['label'])

# Check the mapping of classes to numeric values
print("Class mapping:", dict(zip(le.classes_, le.transform(le.classes_))))

# Step 2: Prepare the image data (resize and normalize images)
images = []
labels = df['label'].values  # Get the encoded labels

# Loop through each image data in the 'image' column and preprocess the images
for image_data in df['image']:  # Assuming the image data is in 'image' column (PIL image)
    img = image_data.convert('RGB')  # Ensure the image is in RGB format
    img = img.resize((224, 224))  # Resize to the input size required for the model
    img = np.array(img)  # Convert PIL image to numpy array
    img = img / 255.0  # Normalize pixel values to [0, 1]
    images.append(img)

# Convert the list of images to a numpy array
images = np.array(images, dtype="float32")

# Step 3: Split the dataset into training and testing sets with random_state=1000
X_train, X_test, y_train, y_test = train_test_split(images, labels, test_size=0.2, random_state=1000)

# Step 4: Build a simple CNN model
model = tf.keras.Sequential([
    tf.keras.layers.InputLayer(input_shape=(224, 224, 3)),  # Image input layer (RGB)

    # Convolutional layers
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),

    tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),

    tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),

    # Flatten and dense layers
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(len(le.classes_), activation='softmax')  # Number of classes
])

# Step 5: Compile the model
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Step 6: Train the model without data augmentation
history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=10, batch_size=32)

# Step 7: Evaluate the model
test_loss, test_acc = model.evaluate(X_test, y_test)
print(f"Test accuracy: {test_acc:.2f}")

plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)  # 1 row, 2 columns, first subplot
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Training vs Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

# Plotting training and validation loss
plt.subplot(1, 2, 2)  # 1 row, 2 columns, second subplot
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Training vs Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

# Display the plots
plt.tight_layout()  # Adjust layout for better spacing
plt.show()

test_loss, test_accuracy = model.evaluate(X_test, y_test, batch_size=32)

print(f"Test Loss: {test_loss}")
print(f"Test Accuracy: {test_accuracy}")

X_test = X_test.astype('float32')  # Ensure test data is float32
y_test = y_test.astype('int32')

def test_data_generator(X, y, batch_size):
    dataset_size = len(X)
    indices = np.arange(dataset_size)
    while True:
        for start_idx in range(0, dataset_size, batch_size):
            end_idx = min(start_idx + batch_size, dataset_size)
            excerpt = indices[start_idx:end_idx]
            yield X[excerpt], y[excerpt]

test_dataset = tf.data.Dataset.from_generator(
    lambda: test_data_generator(X_test, y_test, batch_size),
    output_signature=(
        tf.TensorSpec(shape=(None, 176, 176, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None,), dtype=tf.int32)
    )
).prefetch(tf.data.AUTOTUNE)

batch_size = 32  # You can adjust this value as needed

# Calculate steps per epoch
steps_per_epoch = len(X_test) // batch_size
print("Steps per epoch for test dataset:", steps_per_epoch)

from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D

# Load InceptionV3 without the top layer
base_model = InceptionV3(weights='imagenet', include_top=False, input_shape=(176, 176, 3))

# Add custom layers
x = base_model.output
x = GlobalAveragePooling2D()(x)  # Global average pooling to reduce dimensions
x = Dense(1024, activation='relu')(x)  # Add a fully connected layer
predictions = Dense(4, activation='softmax')(x)  # Final layer with 4 classes

# Create the model
model_Inception = Model(inputs=base_model.input, outputs=predictions)

# Optionally, freeze the base model layers
for layer in base_model.layers:
    layer.trainable = False  # Freeze the layers of InceptionV3

# Compile the model
model_Inception.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Summary of the model
model_Inception.summary()

# Predict on the test data
predictions = model.predict(X_test)

# If you want to display some predictions with the corresponding actual labels
for i in range(5):  # Display first 5 predictions
    predicted_class = np.argmax(predictions[i])  # Get the predicted class
    actual_class = np.argmax(y_test[i])  # Get the actual class
    print(f"Predicted: {predicted_class}, Actual: {actual_class}")