from ultralytics import YOLO

# model=YOLO("./runs/detect/train10/weights/best.onnx")
model=YOLO("./runs/detect/train13/weights/best.pt")

model.export(format="ncnn")