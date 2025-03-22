import librosa
import librosa.display
import random
import os
import wave
import pandas as pd
import shutil
from scipy.io import wavfile
import soundfile as sf
from collections import defaultdict
import numpy as np
import json
from tqdm import tqdm

# Loading Data
patient_diagnosis_info = pd.read_csv(r'C:\Users\Jiary\Documents\GitHub\ML\csv_data\patient_diagnosis_filtered_data.csv',
                                     names=['pid', 'disease'])
print(patient_diagnosis_info.head())

total_patient_per_disease = patient_diagnosis_info['disease'].value_counts().to_dict()
print(f'Total Cases: {sum(total_patient_per_disease.values())}')

audio_dir = r'C:\Users\Jiary\Documents\GitHub\ML\Processed_Audio_Files'
output_audio_dir = r'C:\Users\Jiary\Documents\GitHub\ML\Final_Audio_Dataset'
os.makedirs(output_audio_dir, exist_ok=True)

disease_count = defaultdict(int)
disease_files = defaultdict(list)

# Organize files by disease
for audio_file in os.listdir(audio_dir):
    parts = audio_file.split('_')
    pid = int(parts[0])
    disease = patient_diagnosis_info.loc[patient_diagnosis_info['pid'] == pid, 'disease'].values[0]
    disease_count[disease] += 1
    disease_files[disease].append(os.path.join(audio_dir, audio_file))
for disease, count in disease_count.items():
    print(f'Number of Audio Samples: {count}, Disease: {disease}')
# Copy original files to output folder
for disease, files in disease_files.items():
    for file in files:
        shutil.copy(file, os.path.join(output_audio_dir, os.path.basename(file)))

def time_stretch(audio, rate=1.0):
    return librosa.effects.time_stretch(audio, rate=rate)

def pitch_shift(audio, sr, n_steps=4):
    return librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_steps)

def add_noise(audio, noise_level=0.005):
    noise = np.random.randn(len(audio)) * noise_level
    return np.clip(audio + noise, -1, 1)

def save_audio(audio, sr, output_path):
    sf.write(output_path, audio, sr)

def augment_audio(file_path, output_dir, sr=22050, augmentation_id=1):
    try:
        audio, sr = librosa.load(file_path, sr=sr)
        if len(audio) < sr:
            print(f"Skipping {file_path}: File too short.")
            return None
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        augmented_file_name = f"{base_name}_aug{augmentation_id}.wav"
        output_path = os.path.join(output_dir, augmented_file_name)
        
        rate = np.random.uniform(0.8, 1.2)
        n_steps = np.random.randint(-4, 4)
        noise_level = np.random.uniform(0.001, 0.01)

        augmented_audio = time_stretch(audio, rate=rate)
        augmented_audio = pitch_shift(augmented_audio, sr, n_steps=n_steps)
        augmented_audio = add_noise(augmented_audio, noise_level=noise_level)
        
        save_audio(augmented_audio, sr, output_path)
        return output_path
    except Exception as e:
        print(f"Error augmenting {file_path}: {e}")
        return None

def augment_class(audio_dir, output_dir, disease_files, num_files_to_augment=10, log_file='augmented_audio_log.json'):
    os.makedirs(output_dir, exist_ok=True)
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            augmented_files = json.load(f)
    else:
        augmented_files = []
    
    files_to_augment = [f for f in disease_files if f not in augmented_files]
    selected_files = random.sample(files_to_augment, min(len(files_to_augment), num_files_to_augment))
    
    for file_path in tqdm(selected_files, desc=f"Augmenting"):
        for aug_id in range(1, 6):
            output_path = augment_audio(file_path, output_dir, augmentation_id=aug_id)
            if output_path:
                augmented_files.append(file_path)

    with open(log_file, 'w') as f:
        json.dump(augmented_files, f)

minority_classes = ["Bronchiectasis", "Pneumonia", "Bronchiolitis", "URTI", "Healthy"]
for disease in minority_classes:
    print(f"Augmenting {disease}...")
    augment_class(audio_dir, output_audio_dir, disease_files[disease], num_files_to_augment=50)
