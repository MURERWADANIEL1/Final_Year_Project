import os
import pandas as pd
import numpy as np
import librosa
from collections import defaultdict
import matplotlib.pyplot as plt

# Function to count audio files in a directory
def count_audio_files(directory):
    return len([f for f in os.listdir(directory) if f.endswith('.wav')])

# Loading Data
patient_diagnosis_info = pd.read_csv(r'C:\Users\Jiary\Documents\GitHub\ML\csv_data\patient_diagnosis_filtered_data.csv',
                                     names=['pid', 'disease'])
print(patient_diagnosis_info.head())

total_patient_per_disease = patient_diagnosis_info['disease'].value_counts().to_dict()
print(f'Total Cases: {sum(total_patient_per_disease.values())}')

# Define directories
initial_audio_data = r'C:\Users\Jiary\Documents\GitHub\ML\Processed_Audio_Files'
audio_dir = r'C:\Users\Jiary\Documents\GitHub\ML\Final_Audio_Dataset'

# Count audio files in both directories
initial_audio_count = count_audio_files(initial_audio_data)
final_audio_count = count_audio_files(audio_dir)

print(f'Number of audio files in Processed_Audio_Files: {initial_audio_count}')
print(f'Number of audio files in Final_Audio_Dataset: {final_audio_count}')

# Function to organize files by disease
def organize_files_by_disease(directory, patient_diagnosis_info):
    disease_count = defaultdict(int)
    disease_files = defaultdict(list)

    for audio_file in os.listdir(directory):
        if audio_file.endswith('.wav'):  # Ensure only audio files are processed
            parts = audio_file.split('_')
            pid = int(parts[0])
            disease = patient_diagnosis_info.loc[patient_diagnosis_info['pid'] == pid, 'disease'].values[0]
            disease_count[disease] += 1
            disease_files[disease].append(os.path.join(directory, audio_file))
    
    return disease_count, disease_files

# Organize files by disease for Processed_Audio_Files
processed_disease_count, processed_disease_files = organize_files_by_disease(initial_audio_data, patient_diagnosis_info)

# Organize files by disease for Final_Audio_Dataset
final_disease_count, final_disease_files = organize_files_by_disease(audio_dir, patient_diagnosis_info)

# Print disease-wise counts for Processed_Audio_Files
print("\nDisease-wise counts for Processed_Audio_Files:")
for disease, count in processed_disease_count.items():
    print(f'Number of Audio Samples: {count}, Disease: {disease}')

# Print disease-wise counts for Final_Audio_Dataset
print("\nDisease-wise counts for Final_Audio_Dataset:")
for disease, count in final_disease_count.items():
    print(f'Number of Audio Samples: {count}, Disease: {disease}')

# Visualization for Processed_Audio_Files
plt.figure(figsize=(10, 6))
plt.bar(processed_disease_count.keys(), processed_disease_count.values(), color='skyblue')
plt.xlabel('Disease')
plt.ylabel('Number of Audio Samples')
plt.title('Distribution of Audio Samples by Disease (Processed_Audio_Files)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Visualization for Final_Audio_Dataset
plt.figure(figsize=(10, 6))
plt.bar(final_disease_count.keys(), final_disease_count.values(), color='lightgreen')
plt.xlabel('Disease')
plt.ylabel('Number of Audio Samples')
plt.title('Distribution of Audio Samples by Disease (Final_Audio_Dataset)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


def extract_features(filepath):
    y,sr=librosa.load(filepath, sr=None)
    features={
        'zero_crossing_rate':np.mean(librosa.feature.zero_crossing_rate(y)[0]),
        'rms_energy': np.mean(librosa.feature.rms(y)[0]),
        'spectral_centroid': np.mean(librosa.feature.spectral_centroid(y, sr=sr)[0]),
        'spectral_bandwidth': np.mean(librosa.feature.spectral_bandwidth(y, sr=sr)[0]),
        'spectral_rolloff':np.mean(librosa.feature.spectral_rolloff(y, sr=sr)[0]),
        'mfccs':np.mean(librosa.feature.mfcc(y, sr=sr, n_mfcc=13).T, axis=0),
        'tempo':librosa.beat.tempo(y, sr=sr)[0]
        
    }
    return features
all_features=[]

for audio_file in os.listdir(output_audio_dir):
    if audio_file.endswith('.wav'):
        audio_path=os.path.join(output_audio_dir, audio_file)
        features=extract_features(audio_path)
        print('processing', {audio_file})
        all_features.append(features)

features_df=pd.DataFrame(all_features)
features_df.to_csv('features.csv', index=False)
print('Features extracted and saved to features.csv')
print(features_df.head()) 

# Plot the waveform and spectral features for one file
file_path = os.path.join(audio_dir, os.listdir(audio_dir)[0])  # First file
y, sr = librosa.load(file_path)

plt.figure(figsize=(14, 8))

# Waveform
plt.subplot(3, 1, 1)
librosa.display.waveshow(y, sr=sr)
plt.title('Waveform')

# Spectrogram
plt.subplot(3, 1, 2)
D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
plt.title('Spectrogram')

# MFCCs
plt.subplot(3, 1, 3)
mfccs = librosa.feature.mfcc(y, sr=sr, n_mfcc=13)
librosa.display.specshow(mfccs, x_axis='time')
plt.title('MFCCs')

plt.tight_layout()
plt.show()
