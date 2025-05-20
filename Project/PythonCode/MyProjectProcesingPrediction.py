import numpy as np
import librosa
import matplotlib.pyplot as plt
import librosa.display
from datetime import datetime
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model
import os

# Load label encoder manually
disease_classes = ["URTI", "Healthy", "COPD", "Bronchiectasis", "Pneumonia", "Bronchiolitis"]
CONFIDENCE_THRESHOLD = 0.7  # 70% minimum confidence
MIN_DURATION_SEC = 0.5


def add_noise(data):
    noise_value = 0.015 * np.random.uniform() * np.amax(data)
    return data + noise_value * np.random.normal(size=data.shape[0])

def stretch_process(data, rate=0.8):
    return librosa.effects.time_stretch(data, rate=rate)

def pitch_process(data, sampling_rate, pitch_factor=0.7):
    return librosa.effects.pitch_shift(data, sr=sampling_rate, n_steps=pitch_factor)

def extract_process(data, sample_rate):
    output_result = np.array([])

    mean_zero = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
    output_result = np.hstack((output_result, mean_zero))

    stft_out = np.abs(librosa.stft(data))
    chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft_out, sr=sample_rate).T, axis=0)
    output_result = np.hstack((output_result, chroma_stft))

    mfcc_out = np.mean(librosa.feature.mfcc(y=data, sr=sample_rate, n_mfcc=40).T, axis=0)
    output_result = np.hstack((output_result, mfcc_out))

    root_mean_out = np.mean(librosa.feature.rms(y=data).T, axis=0)
    output_result = np.hstack((output_result, root_mean_out))

    mel_spectrogram = np.mean(librosa.feature.melspectrogram(y=data, sr=sample_rate).T, axis=0)
    output_result = np.hstack((output_result, mel_spectrogram))

    return output_result

def extract_features(file_name):
    try:
        audio, sample_rate = librosa.load(file_name, sr=None)  # Load full file with native rate
        if len(audio) == 0:
            print("Loaded audio is empty.")
            return None
        features = extract_process(audio, sample_rate)
        return features
    except Exception as e:
        print("Error extracting features:", e)
        return None

def save_spectrogram_data_and_image(audio_path, S_DB, predicted_class):
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_dir = "Saved_Spectrograms"
    os.makedirs(output_dir, exist_ok=True)

    # New filename: PredictedClass_OriginalName
    filename_base = f"{predicted_class}_{base_name}"

    # Save .npy file
    npy_path = os.path.join(output_dir, f"{filename_base}.npy")
    np.save(npy_path, S_DB)
    print(f"Raw spectrogram saved: {npy_path}")

    # Save .png image
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S_DB, sr=22050, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title(f"Mel Spectrogram - {predicted_class}")
    plt.tight_layout()

    png_path = os.path.join(output_dir, f"{filename_base}.png")
    plt.savefig(png_path)
    plt.close()
    print(f"Visual spectrogram saved: {png_path}")


def predict(file_path, model, scaler, label_classes):
    try:
        audio, sample_rate = librosa.load(file_path, sr=None)
        duration_sec = len(audio) / sample_rate
        print(f"Loaded audio duration: {duration_sec:.2f} seconds (Sample rate: {sample_rate})")

        if duration_sec < MIN_DURATION_SEC:
            print(f"Audio is shorter than {MIN_DURATION_SEC} seconds. Prediction aborted.")
            return None

        # Waveform
        plt.figure(figsize=(12, 3))
        librosa.display.waveshow(audio, sr=sample_rate)
        plt.title("Waveform")
        plt.tight_layout()
        plt.show()

        # Mel Spectrogram
        S = librosa.feature.melspectrogram(y=audio, sr=sample_rate)
        S_DB = librosa.power_to_db(S, ref=np.max)

        plt.figure(figsize=(12, 4))
        librosa.display.specshow(S_DB, sr=sample_rate, x_axis='time', y_axis='mel')
        plt.colorbar(format='%+2.0f dB')
        plt.title("Mel Spectrogram")
        plt.tight_layout()
        plt.show()

        # Extract features and predict
        features = extract_process(audio, sample_rate)
        features_scaled = scaler.transform([features])
        features_scaled = np.expand_dims(features_scaled, axis=2)

        prediction = model.predict(features_scaled)
        predicted_index = np.argmax(prediction)
        confidence = np.max(prediction)

        if confidence < CONFIDENCE_THRESHOLD:
            print(f"Low confidence ({confidence:.2%}). Prediction rejected.")
            return "Unknown", confidence

        predicted_class = label_classes[predicted_index]

        # Now safe to save
        save_spectrogram_data_and_image(file_path, S_DB, predicted_class)

        print(f"Predicted class: {predicted_class}")
        print(f"Confidence: {confidence:.2%}")
        return predicted_class, confidence

    except Exception as e:
        print("Error during prediction:", e)
        return None
# Load StandardScaler and set its parameters
scaler = StandardScaler()
scaler.mean_ = np.load(r"C:\Users\Jiary\Documents\GitHub\ML\Project\PythonCode\scaler_mean.npy")
scaler.scale_ = np.load(r"C:\Users\Jiary\Documents\GitHub\ML\Project\PythonCode\scaler_scale.npy")
scaler.var_ = scaler.scale_ ** 2

# Load trained model
model_path = r"C:\Users\Jiary\Documents\GitHub\ML\Project\Model\respiratory.model.h5"
model = load_model(model_path)
print("Model loaded.")

# Set up path to latest audio file
recording_dir = r"C:\Users\Jiary\Documents\GitHub\ML\recordings"
latest_recording = max(
    [f for f in os.listdir(recording_dir) if f.endswith('.wav')],
    key=lambda x: os.path.getctime(os.path.join(recording_dir, x))
)
audio_path = os.path.join(recording_dir, latest_recording)

# Run prediction
predict(audio_path, model, scaler, disease_classes)
