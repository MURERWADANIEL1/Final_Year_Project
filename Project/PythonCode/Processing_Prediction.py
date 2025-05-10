import os
import librosa
import numpy as np
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import librosa.display
from datetime import datetime

# Configuration
CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence (70%) - adjust based on your 86% test accuracy
disease_classes = ["URTI", "Healthy", "COPD", "Bronchiectasis", "Pneumonia", "Bronchiolitis"]
label_encoder = LabelEncoder()
label_encoder.fit(disease_classes)

def create_spectrogram(audio_path, target_shape=(128, 128)):
    """Create mel spectrogram matching training process"""
    try:
        y, sr = librosa.load(audio_path, sr=None)
        s = librosa.feature.melspectrogram(y=y, sr=sr)
        s_db = librosa.amplitude_to_db(s, ref=np.max)
        s_resized = cv2.resize(s_db, target_shape)
        return np.expand_dims(s_resized, axis=-1)
    except Exception as e:
        print(f"Error creating spectrogram: {str(e)}")
        return None

def visualize_prediction(prediction, spectrogram, disease, confidence):
    
    """Visualize both spectrogram and class probabilities"""
    plt.figure(figsize=(15, 5))
    
    # Spectrogram plot
    plt.subplot(1, 2, 1)
    librosa.display.specshow(spectrogram[:,:,0], x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    title = f"Predicted: {disease} ({confidence:.2%})"
    if disease == "Unknown":
        title += "\n(Low confidence)"
    plt.title(title)
    
    # Class probabilities plot
    plt.subplot(1, 2, 2)
    classes = label_encoder.classes_
    probabilities = prediction[0]
    colors = ['green' if prob == max(probabilities) else 'blue' for prob in probabilities]
    bars = plt.barh(classes, probabilities, color=colors)
    plt.xlim([0, 1])
    plt.title('Class Probabilities')
    plt.xlabel('Probability')
    
    # Annotate probabilities
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.01, bar.get_y() + bar.get_height()/2,
                f'{width:.2%}', ha='left', va='center')
    
    plt.tight_layout()
    plt.show()
def preprocess_spectrogram(spectrogram):
    """Normalize and scale spectrogram if needed"""
    scaler = MinMaxScaler()
    original_shape = spectrogram.shape
    spectrogram_flat = spectrogram.reshape(-1, 1)
    spectrogram_scaled = scaler.fit_transform(spectrogram_flat)
    spectrogram_normalized = spectrogram_scaled.reshape(original_shape)
    return spectrogram_normalized


def predict_disease(audio_path, model):
    """Predict disease with confidence thresholding"""
    spectrogram = create_spectrogram(audio_path)
    if spectrogram is None:
        return None, None, None, None
    
    spectrogram_processed = preprocess_spectrogram(spectrogram)
    spectrogram_input = np.expand_dims(spectrogram_processed, axis=0)
    
    prediction = model.predict(spectrogram_input, verbose=0)
    predicted_class = np.argmax(prediction, axis=1)
    confidence = np.max(prediction)
    
    # Apply confidence threshold
    if confidence < CONFIDENCE_THRESHOLD:
        return "Unknown", confidence, spectrogram, prediction
    
    predicted_disease = label_encoder.inverse_transform(predicted_class)[0]
    return predicted_disease, confidence, spectrogram, prediction

def save_prediction_results(audio_path, disease, confidence, spectrogram):
    """Save results with formatted filenames"""
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_dir = "Predicted_Spectrograms"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save spectrogram
    spectrogram_filename = f"{base_name}_{disease}.npy"
    spectrogram_path = os.path.join(output_dir, spectrogram_filename)
    np.save(spectrogram_path, spectrogram)
    print(f"\nSaved spectrogram as: {spectrogram_filename}")

def main():
    try:
        model = tf.keras.models.load_model(r'C:\Users\Jiary\Documents\GitHub\ML\Project\Model\respiratory_cnn_model.h5')
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return
    
    # Get latest recording
    recording_dir = r"C:\Users\Jiary\Documents\GitHub\ML\recordings" 
    wav_files = [f for f in os.listdir(recording_dir) if f.endswith('.wav')]
    
    if not wav_files:
        print("No recording found in directory")
        return
    
    latest_recording = max(wav_files, key=lambda x: os.path.getctime(os.path.join(recording_dir, x)))
    audio_path = os.path.join(recording_dir, latest_recording)
    print(f"\nProcessing recording: {latest_recording}")
    
    # Make prediction
    disease, confidence, spectrogram, prediction = predict_disease(audio_path, model)
    
    if disease is None:
        print("Could not process audio file")
        return
    
    # Display results
    print(f"\nPrediction Results:")
    print(f"Top Prediction: {disease}")
    print(f"Confidence: {confidence:.2%}")
    if disease == "Unknown":
        print(f"Note: Below confidence threshold ({CONFIDENCE_THRESHOLD:.0%})")
    
    # Visualize results
    visualize_prediction(prediction, spectrogram, disease, confidence)
    
    # Save results
    save_prediction_results(audio_path, disease, confidence, spectrogram)

if __name__ == "__main__":
    main()