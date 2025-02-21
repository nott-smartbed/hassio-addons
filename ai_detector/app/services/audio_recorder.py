from pvrecorder import PvRecorder
import numpy as np
import time
import soundfile as sf

class AudioRecorder:
    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.FRAME_LENGTH = 512
    
    def get_available_devices(self):
        """Returns a list of available audio devices."""
        self.devices = []
        for index, device in enumerate(PvRecorder.get_available_devices()):
            print(f"[{index}] {device}")
            self.devices.append(device)
        return self.devices
    

    def record_audio(self, device_index: int = -1, duration: int = 3):
        """Record audio from the specified device."""
        recorder = PvRecorder(device_index=device_index, frame_length=self.FRAME_LENGTH)
        try:
            audio = []
            recorder.start()
            print("🎤 Listening... Press Ctrl+C to stop.")
            start_time = time.time()
            while time.time() - start_time < duration:
                frame = np.array(recorder.read(), dtype=np.float32) / 32768.0
                audio.extend(frame)
            recorder.stop()
        except KeyboardInterrupt:
            recorder.stop()
        finally:
            recorder.delete()
            print("Recording stopped.")
            return audio