from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QProgressBar
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
import psutil
from PyQt6.uic import loadUi
from time import time
import sys
import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from skimage.feature import local_binary_pattern
import joblib
from scipy.special import expit
import mysql.connector

class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        loadUi("UI(user Interface)/MainQt.ui", self)
        
        self.camera_label1 = self.findChild(QLabel, 'CAMERA1')
        self.camera_label2 = self.findChild(QLabel, 'CAMERA2')

     # Find the progress bars and check if they are loaded properly
        # camera1    
        self.class_a_progress = self.findChild(QProgressBar, 'progressBarA')  
        self.class_b_progress = self.findChild(QProgressBar, 'progressBarB')  
        # camera2
        self.class_a_progress2 = self.findChild(QProgressBar, 'progressBar_2A')  
        self.class_b_progress2 = self.findChild(QProgressBar, 'progressBar_2B')  

        self.cap1 = cv2.VideoCapture(0)
        self.cap2 = cv2.VideoCapture(2)

        # Load the YOLO model
        self.model = YOLO('./runs/detect/train12/weights/best_ncnn_model')

        # self.db_connection = mysql.connector.connect(
        #     host="localhost",
        #     user="root",  # Your MySQL username
        #     password="",  # Your MySQL password (leave blank if no password)
        #     database="record"  # The database you created
        # )

    

        # Load the trained SVM model and scaler
        self.svm_model = joblib.load('svm_banana_model.pkl')  # Replace with your SVM model path
        self.scaler = joblib.load('scaler_banana.pkl')  # Replace with your scaler path

        # LBP parameters
        self.radius = 3
        self.n_points = 8 * self.radius

        # Set up a QTimer to call the update_frame method periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame1)
        self.timer.start(30)  # Update every 30ms

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame2)
        self.timer.start(30)

        self.Run_ing = QTimer(self)
        self.Run_ing.timeout.connect(self.RPB_sync)
        self.Run_ing.start(1000)

    def extract_lbp_features(self, image, radius, n_points):
        lbp = local_binary_pattern(image, n_points, radius, method="uniform")
        (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, n_points + 3), range=(0, n_points + 2))
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-6)  # Normalize the histogram
        return hist

    def classify_banana(self, image, svm_model, scaler, radius, n_points):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lbp_features = self.extract_lbp_features(gray_image, radius, n_points)
        lbp_features_scaled = scaler.transform([lbp_features])  # Scale the features
        decision = svm_model.decision_function(lbp_features_scaled)
        probability = expit(decision)[0]  # Convert decision score to probability
        prediction = svm_model.predict(lbp_features_scaled)
        return prediction[0], probability

       
    
#  cam 1////////////////////////////////////////////////////////////////////
    def update_frame1(self):
        ret, frame1 = self.cap1.read()
        if not ret:
            return
         # Read class labels from file
        with open("dataset/classes.txt", "r") as my_file:
            class_list = my_file.read().split("\n")    

        frame1 = cv2.resize(frame1, (393, 246))

        # Perform YOLO detection
        start_time = time()
        results = self.model.predict(frame1)
        detections = results[0].boxes.data.cpu().numpy()  # Get the detection results
        boxes = results[0].boxes.xyxy.cpu() 
        confidences = results[0].boxes.conf.cpu()
        class_ids = results[0].boxes.cls.cpu()  # Class IDs

        # for yolo line
     # Create a DataFrame from the results
        px = pd.DataFrame(boxes.numpy()).astype("float")

        for index, row in px.iterrows():
            x1, y1, x2, y2 = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            cls_id = int(class_ids[index])
            # cls_name = class_list[cls_id]
            confidence = float(confidences[index])
            
            if cls_id == 2:  # Class A
                self.class_a_progress.setValue(int(confidence * 100))
            elif cls_id==0 or cls_id==1:  # Class B
                self.class_b_progress.setValue(int(confidence * 100))
          

        # for svm line
        for (x1, y1, x2, y2, conf, cls) in detections:
            # Extract the detected banana region
            banana_region = frame1[int(y1):int(y2), int(x1):int(x2)]

            # Classify the banana region using the SVM model
            banana_class, probability = self.classify_banana(banana_region, self.svm_model, self.scaler, self.radius, self.n_points)
                

            # Draw the bounding box and class label with confidence score on the frame
            # label = f'Class A: {probability:.2f}' if banana_class == 0 else f'Class B: {probability:.2f}'
            color = (0, 255, 0) if banana_class == 0 else (0, 0, 255)
            cv2.rectangle(frame1, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            # cv2.putText(frame1, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        end_time = time()
        frame_duration = end_time - start_time
        fps = 1 / frame_duration
        self.label_8.setText(f"{int(fps)}%")
        self.stylesheet_FPS = """
                #RPB_PATH_3{
                    background-color: qconicalgradient(cy:0.5, cx:0.5, angle:90, stop:{fps_stop1}
                    rgba(165, 216, 234, 77), stop:{fps_stop2} rgba(166, 226, 228, 2));
                }
            """

        val_fps = min(fps, 60) / 60.0  # Assuming max FPS is 60 for the progress bar
        value_fps = str(val_fps - 0.001)
        self.New_stylesheet_FPS = self.stylesheet_FPS.replace("{fps_stop1}", str(val_fps)).replace("{fps_stop2}", value_fps)
        self.RPB_PATH_3.setStyleSheet(self.New_stylesheet_FPS)

        # Convert the frame to a QImage
        rgb_frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame1.shape
        bytes_per_line = ch * w
        q_img1 = QImage(rgb_frame1.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Set the QImage to the QLabel
        self.camera_label1.setPixmap(QPixmap.fromImage(q_img1))

# cam2 ////////////////////////////////////////////////////
    def update_frame2(self):
        ret, frame2 = self.cap2.read()
        if not ret:
            return

        frame2 = cv2.resize(frame2, (393, 246))

        # Perform YOLO detection
        start_time2 = time()
        results = self.model.predict(frame2)
        detections = results[0].boxes.data.cpu().numpy()  # Get the detection results
        boxes = results[0].boxes.xyxy.cpu() 
        confidences = results[0].boxes.conf.cpu()
        class_ids = results[0].boxes.cls.cpu()  # Class IDs

        # for yolo line
        # Create a DataFrame from the results
        px = pd.DataFrame(boxes.numpy()).astype("float")

        for index, row in px.iterrows():
            x1, y1, x2, y2 = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            cls_id = int(class_ids[index])
            # cls_name = class_list[cls_id]
            confidence = float(confidences[index])
            
            if cls_id == 2:  # Class A
                self.class_a_progress2.setValue(int(confidence * 100))
            elif cls_id==0 or cls_id==1:  # Class B
                self.class_b_progress2.setValue(int(confidence * 100))
        


        # SVM line
        for (x1, y1, x2, y2, conf, cls) in detections:
            # Extract the detected banana region
            banana_region = frame2[int(y1):int(y2), int(x1):int(x2)]

            # Classify the banana region using the SVM model
            banana_class, probability = self.classify_banana(banana_region, self.svm_model, self.scaler, self.radius, self.n_points)



            # if banana_class == 0:  # Class A
            #     self.class_a_progress2.setValue(int(probability * 100))
            # else:  # Class B
            #     self.class_b_progress2.setValue(int(probability * 100))

            # Draw the bounding box and class label with confidence score on the frame
            # label = f'Class A: {probability:.2f}' if banana_class == 0 else f'Class B: {probability:.2f}'
            color = (0, 255, 0) if banana_class == 0 else (0, 0, 255)
            cv2.rectangle(frame2, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            # cv2.putText(frame2, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        end_time2 = time()
        frame_duration2 = end_time2 - start_time2
        fps = 1 / frame_duration2
        self.label_24.setText(f"{int(fps)}%")
        self.stylesheet_FPS2 = """
                #RPB_PATH{
                    background-color: qconicalgradient(cy:0.5, cx:0.5, angle:90, stop:{fps_stop1}
                    rgba(165, 216, 234, 77), stop:{fps_stop2} rgba(166, 226, 228, 2));
                }
            """

        val_fps = min(fps, 60) / 60.0  # Assuming max FPS is 60 for the progress bar
        value_fps = str(val_fps - 0.001)
        self.New_stylesheet_FPS2 = self.stylesheet_FPS2.replace("{fps_stop1}", str(val_fps)).replace("{fps_stop2}", value_fps)
        self.RPB_PATH.setStyleSheet(self.New_stylesheet_FPS2)

        # Convert the frame to a QImage
        rgb_frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame2.shape
        bytes_per_line = ch * w
        q_img2 = QImage(rgb_frame2.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Set the QImage to the QLabel
        self.camera_label2.setPixmap(QPixmap.fromImage(q_img2))

    def RPB_sync(self):
        self.stylesheet_CPU = """
            #RPB_PATH_5{
                background-color: qconicalgradient(cy:0.5, cx:0.5, angle:-90, stop:{cw_stop1}
                rgba(165, 216, 234, 77), stop:{cw_stop2} rgba(166, 226, 228, 2));
            }
        """
        # getting CPU percentage  
        values1 = psutil.cpu_percent()

        # Dividing value or convert float value for RPB PATH
        val1 = (100 - values1) / 100.0
        value1 = str(val1 - 0.001)

        # Replacing Stylesheet Values
        self.New_stylesheet_CPU = self.stylesheet_CPU.replace("{cw_stop1}", str(val1)).replace("{cw_stop2}", value1)
        # set New styleSheet to RPB_path
        self.RPB_PATH_5.setStyleSheet(self.New_stylesheet_CPU)
        #set RPB Percentage in RPB Label
        self.label_14.setText(f"{int(values1)}%")

        # VRAM
        self.stylesheet_VRAM = """
            #RPB_PATH_4{
                background-color: qconicalgradient(cy:0.5, cx:0.5, angle: 90, stop:{vw_stop1}
                rgba(165, 216, 234, 77), stop:{vw_stop2} rgba(166, 226, 228, 2));
            }
        """
        
        # getting VRAM percentage
        vram_info = psutil.virtual_memory()
        values_vram = vram_info.percent

        # Dividing value or convert float value for RPB PATH
        val_vram = (100 - values_vram) / 100.0
        value_vram = str(val_vram - 0.001)

        # Replacing Stylesheet Values
        self.New_stylesheet_VRAM = self.stylesheet_VRAM.replace("{vw_stop1}", str(val_vram)).replace("{vw_stop2}", value_vram)
        # set New styleSheet to RPB_path
        self.RPB_PATH_4.setStyleSheet(self.New_stylesheet_VRAM)
        #set RPB Percentage in RPB Label
        self.label_4.setText(f"{int(values_vram)}%")

       

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec())
