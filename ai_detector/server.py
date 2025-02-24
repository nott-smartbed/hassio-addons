from fastapi import FastAPI
import logging
import sys
from app.services.snore_detector import SnoreDetector
from app.services.pose_detector import PoseDetector

app = FastAPI()

logger = logging.getLogger('uvicorn.error')

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# # StreamHandler for the console
# stream_handler = logging.StreamHandler(sys.stdout)
# log_formatter = logging.Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
# stream_handler.setFormatter(log_formatter)
# logger.addHandler(stream_handler)

@app.get("/status")
def get_status():
    return {"status": "ok"}


@app.get("/snore-detector/predict")
def predict_snoring():
    detector = SnoreDetector()
    detector.load_model()
    prediction = detector.predict_snoring_realtime_using_sd()
    return prediction


@app.get('/snore-detector/predict-test')
def predict_snoring_test():
    detector = SnoreDetector()
    detector.load_model()
    audio_file = '/app/test_data/wav/snoring.wav'
    prediction = detector.predict_snoring_from_audio_file(audio_file)
    return prediction

@app.get('/pose-detector/predict')
def predict_pose():
    detector = PoseDetector()
    boxes = detector.detect_pose_from_camera()
    return {"boxes": boxes}


@app.get('/pose-detector/predict-test')
def predict_pose_test():
    detector = PoseDetector()
    boxes = detector.detect_pose_with_test_data()
    return {"boxes": boxes}

