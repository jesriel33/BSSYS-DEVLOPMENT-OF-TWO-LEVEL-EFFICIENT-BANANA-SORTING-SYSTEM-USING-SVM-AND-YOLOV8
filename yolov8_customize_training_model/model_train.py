from ultralytics import YOLO

model = YOLO('yolov8m.yaml')

results = model.train(data='data_config.yaml', epochs=100 , imgsz=640 , batch=3 )

