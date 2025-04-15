import tensorflow as tf
import os # Import the os module

# --- Configuration ---
keras_model_path = r"C:\Users\Jiary\Documents\GitHub\ML\Project\respiratory_cnn_model.h5"
# Define where you want to save the TFLite model
tflite_model_dir = r"C:\Users\Jiary\Documents\GitHub\ML\Project"
tflite_model_filename = "respiratory_cnn_model.lite" # Or choose another name like audio2.lite
tflite_model_path = os.path.join(tflite_model_dir, tflite_model_filename)

# --- Conversion ---
try:
    # Create the output directory if it doesn't exist
    os.makedirs(tflite_model_dir, exist_ok=True)
    print(f"Output directory ensured: {tflite_model_dir}")

    # Load the Keras model
    print(f"Loading Keras model from: {keras_model_path}")
    model = tf.keras.models.load_model(keras_model_path)
    print("Keras model loaded successfully.")

    # Create a TFLiteConverter object
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Optional: Apply optimizations (recommended for deployment)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Perform the conversion
    print("Converting model to TensorFlow Lite format...")
    tflite_model = converter.convert()
    print("Conversion successful.")

    # Save the converted model
    print(f"Saving TensorFlow Lite model to: {tflite_model_path}")
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_model)
    print("TensorFlow Lite model saved successfully.")

except FileNotFoundError:
    print(f"Error: Keras model file not found at {keras_model_path}")
except Exception as e:
    print(f"An error occurred during conversion: {e}")

print("\nConversion process finished.")
