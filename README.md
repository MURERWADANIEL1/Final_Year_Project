# Respiratory Sound Classification with ESP32 and Deep Learning

This repository contains the complete codebase for a final year project (2024/2025) focused on classifying respiratory diseases from audio sounds. The system uses an ESP32 microcontroller for data acquisition and a Convolutional Neural Network (CNN) for classification.

## Overview

The project's goal is to create a non-invasive diagnostic aid by analyzing respiratory sounds (like coughs or breathing). An ESP32-based hardware device captures audio, streams it wirelessly via Bluetooth Low Energy (BLE) to a computer, where a Python application processes the sound and predicts a potential respiratory condition.

## Key Features

*   **Wireless Data Acquisition**: An ESP32 microcontroller captures audio and streams it in real-time over BLE.
*   **Signal Processing**: Raw audio is converted into mel spectrograms, which are visual representations of the sound spectrum, suitable for image-based deep learning models.
*   **Deep Learning Classification**: A pre-trained TensorFlow/Keras CNN model classifies the spectrogram to identify conditions such as COPD, Pneumonia, Bronchiectasis, and more.
*   **Instant Feedback**: The system provides an immediate prediction with a confidence score.
*   **Visualization**: Generates and displays plots of the audio spectrogram and the model's prediction probabilities for clear interpretation.

## Project Structure
This section details the role of each folder in the repository.

*   **`./` (Root Directory)**
    *   The main project folder containing this `README.md`, `.gitignore`, and other top-level configuration files.

*   **`Project/`**
    *   The primary container for all functional source code, organized into subdirectories for Python application logic, the ML model, and the C++ firmware.

*   **`Project/PythonCode/`**
    *   Contains the Python scripts that form the core of the desktop application.
    *   `RecordingFile.py`: Manages the asynchronous Bluetooth Low Energy (BLE) connection to the ESP32 using the `bleak` and `asyncio` libraries. It discovers the device, connects to the correct service, and streams audio data, saving it as a `.wav` file into the `recordings/` directory.
    *   `Processing_Prediction.py`: Handles the machine learning pipeline. It loads an audio file, preprocesses it into a mel spectrogram, feeds it to the trained model for inference, and visualizes the prediction results.

*   **`Project/Model/`**
    *   Houses the machine learning model assets.
    *   `respiratory_cnn_model.h5`: The final, trained Keras model file. This portable format contains the model's architecture, weights, and training configuration.
    *   `ModelNotebooks/`: Contains Jupyter Notebooks (`.ipynb` files) used for the development and experimentation phase of the model. This is where data exploration, feature engineering, model architecture design, training, and evaluation take place.

*   **`Project/Cpp-Code/`**
    *   Contains the firmware for the ESP32 microcontroller. This C++/Arduino code is responsible for initializing the microphone, sampling audio at the required rate, and transmitting the data wirelessly over BLE.

*   **`recordings/`**
    *   The default output directory for audio files. When `RecordingFile.py` is run, the captured `.wav` audio clip is saved here, ready for processing.

*   **`Predicted_Spectrograms/`**
    *   The default output directory for prediction artifacts. When `Processing_Prediction.py` runs, it saves the generated mel spectrogram image used for the prediction into this folder. This is useful for debugging, analysis, and record-keeping.

*   **`Circuit-Design/`**
    *   Contains all hardware design files. This includes circuit schematics, PCB layouts, and simulation files created in software like Multisim, Proteus, or KiCad.

## System Workflow

1.  **Capture**: The ESP32 device, equipped with a microphone, records respiratory sounds.
2.  **Transmit**: The `RecordingFile.py` script connects to the ESP32 (`ESP32_ML_PROJECT`) and receives the audio stream over BLE, saving it as a `.wav` file in the `recordings/` directory.
3.  **Process & Predict**: The `Processing_Prediction.py` script automatically loads the latest recording.
4.  **Feature Extraction**: It converts the audio into a mel spectrogram.
5.  **Inference**: The spectrogram is fed into the trained CNN model, which outputs a prediction (e.g., "Healthy", "COPD") and a confidence score.
6.  **Visualize**: The results, including the spectrogram and class probabilities, are displayed in a plot. The predicted spectrogram is also saved for review.

## Prerequisites

*   Python 3.8+
*   A computer with Bluetooth support.
*   The custom ESP32 device, programmed with the corresponding firmware and powered on.
*   **Note on `asyncio`**: This project uses `asyncio` for handling BLE communication. It is part of Python's standard library since version 3.4 and does not require a separate installation.
*   Required Python packages. Install them via pip:
    ```bash
    pip install tensorflow numpy librosa opencv-python matplotlib scikit-learn soundfile bleak jupyter
    ```

## How to Use

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MURERWADANIEL1/Final_Year_Project # Replace with your repo URL if different
    cd Final_Year_Project # Or your repository's root folder name

    ```
2.  **Record Audio**: Power on the ESP32 device. Run the recording script to capture a 15-second audio clip.
    ```bash
    python Project/PythonCode/RecordingFile.py
    ```
3.  **Run Prediction**: Once the recording is saved, run the prediction script. It will automatically find and process the latest audio file.
    ```bash
    python Project/PythonCode/Processing_Prediction.py
    ```
    A window will pop up displaying the diagnostic results and visualizations.
