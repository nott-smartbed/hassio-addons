from ultralytics import YOLO
import cv2
import os
import time
from .homeassistant import update_entity

DEFAULT_FILENAME = os.getcwd() + "/app/camera/capture.jpg"
POSE_FILENAME = os.getcwd() + "/app/camera/pose.jpg"
MEDIA_POSE_FILENAME = '/media/camera/pose.jpg'
POSE_ENTITY_ID = "sensor.pose_detector"

class PoseDetector():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PoseDetector, cls).__new__(cls)
        return cls._instance
    
    def list_available_camera(self):
        index = 0
        available_cameras = []
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.read()[0]:
                break
            else:
                available_cameras.append(index)
            cap.release()
            index += 1
        return available_cameras
    

    def capture_image(self, camera_index, filename=None):
        if filename is None:
            filename = DEFAULT_FILENAME
        
        cap = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return

        ret, frame = cap.read()

        if ret:
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")
        else:
            print("Error: Could not capture image.")

        cap.release()
        cv2.destroyAllWindows()

    
    def load_model(self):
        model_path = os.getcwd() + '/app/models/yolo11n-pose.pt'
        model = YOLO(model_path)
        return model
    
    
    def save_pose_image(self, results):
        results[0].save(filename=POSE_FILENAME)
        results[0].save(filename=MEDIA_POSE_FILENAME)
        print(f"Pose Image saved ")


    def get_pose_image(self):
        return POSE_FILENAME

    def detect_pose_from_camera(self, camera_index=0):
        try:
            model = self.load_model()
            camera_devices = self.list_available_camera()
            if len(camera_devices) == 0:
                print("Error: No camera detected.")
                return None
            if camera_index >= len(camera_devices):
                print(f"Error: Camera index {camera_index} not found. only {len(camera_devices)} camera(s) detected.")
                return None
            self.capture_image(camera_index, DEFAULT_FILENAME)
            results = model(DEFAULT_FILENAME)
            self.save_pose_image(results)
            os.remove(DEFAULT_FILENAME)
            return results
        except Exception as e:
            print(e)
            return None
        
    def update_ha_entity(self, data_payload):
        response = update_entity(POSE_ENTITY_ID, data_payload)
        if not response:
            print(f"Error updating entity {POSE_ENTITY_ID}.")
            return False
        print(f"Entity {POSE_ENTITY_ID} updated.")
        return True