from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import logging
from app.services.pose_detector import PoseDetector
import time, json

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


@app.get('/pose-detector/predict')
def predict_pose():
    detector = PoseDetector()
    started_at = int(time.time())
    results = detector.detect_pose_from_camera()
    if results is None:
        return JSONResponse(status_code=500, content={"error": "No camera detected."})
    if results[0].names.get(0) != "person":
        return JSONResponse(status_code=500, content={"error": "No person detected."})
    entity_data = {
        "state": "ON",
        "attributes": {
            "started_at": started_at,
            "ended_at": int(time.time()),
            "pose_keypoints": json.dumps([[round(float(x), 4), round(float(y), 4)] for x, y in results[0].keypoints.xyn[0]]),
        }
    }
    detector.update_ha_entity(entity_data)
    return JSONResponse(status_code=200, content={"message": "Pose detected successfully."})


@app.get('/pose-detector/pose-image')
def get_latest_pose_image():
    detector = PoseDetector()
    image_path = detector.get_pose_image()
    return FileResponse(image_path)