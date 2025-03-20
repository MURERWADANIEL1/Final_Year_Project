import librosa
import librosa.display
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import shutil

# Function to extract audio features
patient_diagnosis_info=pd.read_csv(r'C:\Users\Jiary\Downloads\archive\Respiratory_Sound_Database\Respiratory_Sound_Database\patient_diagnosis.csv',names=['pid','disease'])
print(patient_diagnosis_info.head())
audio_dir = r'C:\Users\Jiary\Downloads\archive\Respiratory_Sound_Database\Respiratory_Sound_Database\audio_and_txt_files'
print(len(os.listdir(audio_dir)))

df=pd.read_csv(r'C:/Users/Jiary/Downloads/archive/Respiratory_Sound_Database/Respiratory_Sound_Database/audio_and_txt_files/160_1b3_Al_mc_AKGC417L.txt',sep='\t')
df.head()
# Get all the filenames
files = [s.split('.')[0] for s in os.listdir(audio_dir) if '.txt' in s]

def getFilenameInfo(file):
    return file.split('_')

files_data = []
for file in files:
    data = pd.read_csv(audio_dir + file + '.txt', sep='\t', names=['start', 'end', 'crackles', 'wheezles'])
    name_data = getFilenameInfo(file)
    data['pid'] = name_data[0]
    data['mode'] = name_data[-2]
    data['filename'] = file
    files_data.append(data)

files_df = pd.concat(files_data)
files_df.reset_index(inplace=True)
patient_diagnosis_info['pid'] = patient_diagnosis_info['pid'].astype('int32')
files_df['pid'] = files_df['pid'].astype('int32')
data = pd.merge(files_df, patient_diagnosis_info, on='pid')

target_samples = 160
filtered_data = []
for disease in data['disease'].unique():
    disease_data = data[data['disease'] == disease]
    if len(disease_data) >= target_samples:
        filtered_data.append(disease_data.head(target_samples))  

final_data = pd.concat(filtered_data)

os.makedirs('csv_data', exist_ok=True)
final_data.to_csv('csv_data/data_filtered.csv', index=False)



# Create directories for audio and text files
"""
audio_files = os.path.join(audio_dir, 'audio_files')
text_files = os.path.join(audio_dir, 'text_files')

os.makedirs(audio_files, exist_ok=True)
os.makedirs(text_files, exist_ok=True)

# Sort files into respective directories
for filename in os.listdir(audio_dir):
    if filename.endswith('.wav'):
        shutil.move(os.path.join(audio_dir, filename), os.path.join(audio_files, filename))
        
    elif filename.endswith('.txt'):
        shutil.move(os.path.join(audio_dir, filename), os.path.join(text_files, filename))
        

print("Files have been sorted!")

print(len(os.listdir(audio_files)))
print(len(os.listdir(text_files)))
"""
