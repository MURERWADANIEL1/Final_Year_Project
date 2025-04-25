import subprocess

# Run BLE recording
print("=== Starting Recording ===")
subprocess.run(["python", "ble_recorder.py"])

# Run analysis
print("\n=== Starting Analysis ===")
subprocess.run(["python", "analyze_recording.py"])