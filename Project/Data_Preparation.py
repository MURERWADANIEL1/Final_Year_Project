import os
import pandas as pd
import shutil
import numpy as np
from scipy.io import wavfile
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

# Load patient diagnosis information 
patient_diagnosis_info = pd.read_csv(r'C:\Users\Jiary\Documents\GitHub\ML\patient_diagnosis_filtered_data.csv',
    names=['pid', 'disease'])
print(patient_diagnosis_info.head())

audio_dir = r'C:\Users\Jiary\Documents\GitHub\ML\Filtered_audio_files'
print(len(os.listdir(audio_dir)))
annotation_dir=r'C:\Users\Jiary\Documents\GitHub\ML\Filtered_audio_files'

output_audio_dir=r'C:\Users\Jiary\Documents\GitHub\ML\Processed_Audio_Files'
os.makedirs(output_audio_dir, exist_ok=True)

#extract the patient id from the audio file name
def extract_pid(filename):
    
    return filename.split('_')[0]

def get_disease(patient_id, patient_diagnosis_info):
    return patient_diagnosis_info[patient_diagnosis_info['pid']==patient_id]['disease'].values[0]
print(get_disease('200', patient_diagnosis_info))

def load_annotation(file_path):
    columns=['start', 'end', 'crackles', 'wheezle']
    return pd.read_csv(file_path, sep='\t', names=columns)

def segment_audio(audio, sr, start, end):
    start_sample=int(start*sr)
    end_sample=int(end*sr)
    return audio[start_sample:end_sample]


for wav_file in os.listdir(audio_dir):
    if wav_file.endswith('.wav'):
        patient_id = extract_pid(wav_file)
        disease = get_disease(patient_id, patient_diagnosis_info)


        audio_path = os.path.join(audio_dir, wav_file)
        sr, audio= wavfile.read(audio_path)

        txt_file = wav_file.replace('.wav', '.txt')
        annotation_path=os.path.join(audio_dir, txt_file)
        annotation_df=load_annotation(annotation_path)
        
        for idx, row in annotation_df.iterrows():
            start, end, crackles, wheezes=row
            segmented_audio=segment_audio(audio, sr, start, end)
            base_name=os.path.splitext(wav_file)[0]
            segment_name=f'{base_name}_seg{idx}_C{crackles}_W{wheezes}.wav'
            segment_path=os.path.join(output_audio_dir, segment_name)
            wavfile.write(segment_path, sr, segmented_audio)
            print(f'Saved Segment: {segment_name}')
print("Segmentation Complete. Segmented files saved to: ", output_audio_dir)
