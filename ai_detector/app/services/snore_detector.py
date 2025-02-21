import os, io
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from tensorflow import keras
from cryptography.fernet import Fernet
import os
import tempfile
from pvrecorder import PvRecorder
import time

SAMPLE_RATE = 16000  # Sample rate
N_MELS = 128  # Number of Mel filters
DURATION = 1  # Seconds per sample (split longer files)
HOP_LENGTH = 512  # Hop length for spectrogram
FRAME_LENGTH = 512 # Number of samples per frame
DURATION = 1 # Duration in seconds for each prediction
NUM_FRAMES = SAMPLE_RATE * DURATION // FRAME_LENGTH  # Number of frames in 1s

class SnoreDetector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SnoreDetector, cls).__new__(cls)
        return cls._instance
    
    # Decrypt model (only in memory)
    def decrypt_model(self, encrypted_path):
        key = '2uGSvioRgNAVJHGlFP8cexA914hiZLdqxVjJAWi8jUA=Idontw@nt2beche@ted'
        cipher = Fernet(key)
        with open(encrypted_path, "rb") as file:
            decrypted_data = cipher.decrypt(file.read())
        return decrypted_data  # Use this directly without saving

    
    def load_model(self):
        """Load the trained CNN model."""
        model_path = os.getcwd() + '/app/models/snoring_detector_mel_cnn.bin'
        decrypted_model_bytes = self.decrypt_model(model_path)
        # Use a temporary file to store decrypted model
        with tempfile.NamedTemporaryFile(suffix=".keras", delete=True) as tmp_file:
            tmp_file.write(decrypted_model_bytes)
            self.model = keras.models.load_model(tmp_file.name)
        # model.compiled_metrics == None
        # Recompile the model
        self.model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
        print("Model loaded successfully.")

    
    # Function to convert audio to a Mel spectrogram
    def extract_mel_spectrogram(self, file_path, sr=SAMPLE_RATE, n_mels=N_MELS, duration=DURATION):
        y, _ = librosa.load(file_path, sr=sr, mono=True)  # Load as mono
        y = librosa.util.fix_length(y, size=sr * duration)  # Pad/cut to fixed length
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, hop_length=HOP_LENGTH)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)  # Convert to dB scale
        return mel_spec_db
    

    def display_mel_spectrogram(self, file_path):
        mel_spec = self.extract_mel_spectrogram(file_path)
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(mel_spec, sr=SAMPLE_RATE, hop_length=HOP_LENGTH, cmap="magma")
        plt.colorbar(label="dB")
        plt.title("Mel Spectrogram")
        plt.xlabel("Time")
        plt.ylabel("Mel Frequency")
        plt.show()


    def predict_snoring_from_audio_file(self, file_path):
        """Predicts if an audio file contains snoring using the CNN model."""
        mel_spec = self.extract_mel_spectrogram(os.getcwd() + file_path)
        mel_spec = mel_spec.reshape(1, mel_spec.shape[0], mel_spec.shape[1], 1)  # Reshape for CNN
        prediction = self.model.predict(mel_spec)
        print(f"prediction #{prediction[0]}")
        return "Snoring" if prediction[0] > 0.8 else "No Snoring"
    

    def predict_snoring_realtime(self):
        """Predicts snoring in real-time using the CNN model."""
        devices = []
        for index, device in enumerate(PvRecorder.get_available_devices()):
            print(f"[{index}] {device}")
            devices.append(device)
        device_index = None
        for i, device in enumerate(devices):
            if "Usb Audio Device" in device:
                device_index = i
                break
        if device_index is None:
            raise ValueError("Usb Audio Device not found")
        recorder = PvRecorder(device_index=device_index, frame_length=FRAME_LENGTH)
        try:
            audio_buffer = []
            recorder.start()
            print("🎤 Listening...")
            start_time = time.time()
            while time.time() - start_time < 5:
                frame = np.array(recorder.read(), dtype=np.float32) / 32768.0
                audio_buffer.extend(frame)
                if len(audio_buffer) >= SAMPLE_RATE * DURATION:
                    # === Convert to Mel Spectrogram ===
                    audio_chunk = np.array(audio_buffer[:SAMPLE_RATE * DURATION])  # Take the latest 1s of audio
                    audio_buffer = audio_buffer[FRAME_LENGTH:]  # Shift buffer to keep real-time data

                    mel_spectrogram = librosa.feature.melspectrogram(
                        y=audio_chunk, sr=SAMPLE_RATE, n_fft=1024, hop_length=HOP_LENGTH, n_mels=N_MELS
                    )
                    mel_spec = librosa.power_to_db(mel_spectrogram, ref=np.max)  # Convert to dB
                    mel_spec = mel_spec.reshape(1, mel_spec.shape[0], mel_spec.shape[1], 1)  # Reshape for CNN
                    prediction = self.model.predict(mel_spec)
                    if prediction[0] > 0.8:
                        print("Snoring detected!")
            recorder.stop()
        except KeyboardInterrupt:
            recorder.stop()
            print("Recording stopped.")
        except Exception as e:
            print(e)
        finally:
            recorder.delete()
            print("Recorder deleted.")
    