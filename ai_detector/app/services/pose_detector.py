from ultralytics import YOLO
import cv2
import os
import time

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
    

    def capture_image(self, camera_index, filename):
        if not filename:
            print("Error: Please provide a filename.")
            return None
        
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


    def detect_pose_with_test_data(self):
        model = self.load_model()
        test_image_path = os.getcwd() + '/app/test_data/images/sleep1.jpg'
        results = model(test_image_path)
        result_image_path = os.getcwd() + '/app/test_data/results/sleep1.jpg'
        results[0].save(filename=result_image_path)
        return results[0].boxes
    

    def detect_pose_from_camera(self, camera_index=0):
        model = self.load_model()
        timestamp = str(int(time.time()))
        filename = os.getcwd() + "/app/capture/images/" + timestamp + ".jpg"
        self.capture_image(camera_index, filename)
        results = model(filename)
        result_image_path = os.getcwd() + '/app/results/images/' + timestamp + '.jpg'
        results[0].save(filename=result_image_path)
        return results[0].boxes
