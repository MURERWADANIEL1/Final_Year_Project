import os
import shutil
import pandas as pd
import numpy as np

# Load patient diagnosis information
patient_diagnosis_info = pd.read_csv(r'C:\Users\Jiary\Downloads\archive\Respiratory_Sound_Database\Respiratory_Sound_Database\patient_diagnosis.csv',
    names=['pid', 'disease'])
print(patient_diagnosis_info.head())

#working directories
output_dir = r'C:\Users\Jiary\Documents\GitHub\ML'
data_dir=r'C:\Users\Jiary\Downloads\archive\Respiratory_Sound_Database\Respiratory_Sound_Database'
audio_dir = os.path.join(data_dir, "audio_and_txt_files")
output_audio_dir = r'C:\Users\Jiary\Documents\GitHub\ML\Filtered_audio_files'
os.makedirs(output_audio_dir, exist_ok=True)

#check data in my working directory
diagnosis_path = os.path.join(data_dir, "patient_diagnosis.csv")  # Contains patient diagnoses
wav_files = sorted([f for f in os.listdir(audio_dir) if f.endswith(".wav")])
txt_files = sorted([f for f in os.listdir(audio_dir) if f.endswith(".txt")])
print(f"Found {len(wav_files)} audio files and {len(txt_files)} annotation files.")

#dropping asthma with a single case
input_file=patient_diagnosis_info
asthma_rows=input_file[input_file['disease']=='Asthma']
LRTI_rows=input_file[input_file['disease']=='LRTI']
df_filtered=input_file[(input_file['disease']!='Asthma') & (input_file['disease']!='LRTI')]
output_file_path=os.path.join(output_dir,'patient_diagnosis_filtered_data.csv')
df_filtered.to_csv(output_file_path, index=False)
print("Asthma rows dropped. Number of rows dropped: ", len(asthma_rows))
print("Number of LRTI rows dropped: ", len(LRTI_rows))
print("Filtered dataset saved to: ", output_dir) 

#dropping audio and text files for asthma
asthma_pids= set(patient_diagnosis_info[patient_diagnosis_info['disease']=='Asthma']['pid'].astype(str))
LRTI_pids= set(patient_diagnosis_info[patient_diagnosis_info['disease']=='LRTI']['pid'].astype(str))
pids_to_remove=asthma_pids.union(LRTI_pids)
print("Total number of patients to remove: ", len(pids_to_remove))

def is_file_to_remove(filename, pid_to_remove):
    patient_id=filename.split('_')[0]
    return patient_id in pid_to_remove
    
for file in wav_files + txt_files:
    if not is_file_to_remove(file, pids_to_remove):
        src_path=os.path.join(audio_dir, file)
        dst_path=os.path.join(output_audio_dir, file)
        shutil.copy(src_path, dst_path)

    else:
        print(f"File {file} is from an asthma or LRTI patient. Skipping.")
print("Filtered audio files saved to: ", output_audio_dir)
