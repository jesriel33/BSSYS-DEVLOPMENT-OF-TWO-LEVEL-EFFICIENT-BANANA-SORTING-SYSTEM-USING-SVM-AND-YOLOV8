import os
import cv2
import numpy as np
from skimage.feature import local_binary_pattern
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import joblib

def compute_lbp(image, num_points=24, radius=8):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray_image, num_points, radius, method='uniform')
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, num_points + 3), range=(0, num_points + 2))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-6)
    return hist

def load_images_from_directory(directory):
    image_paths = []
    labels = []
    for label_dir in os.listdir(directory):
        label_path = os.path.join(directory, label_dir)
        if os.path.isdir(label_path):
            for image_name in os.listdir(label_path):
                image_path = os.path.join(label_path, image_name)
                image_paths.append(image_path)
                labels.append(label_dir)  # Assuming directory names are the labels
    return image_paths, labels

# Load images and labels from directories
train_dir = 'SVMDATA/images/train/'
image_paths, labels = load_images_from_directory(train_dir)

# Convert labels to numerical format
unique_labels = list(set(labels))
label_to_num = {label: num for num, label in enumerate(unique_labels)}
num_labels = [label_to_num[label] for label in labels]

# Compute LBP features for each image
lbp_features = []
for path in image_paths:
    image = cv2.imread(path)
    lbp = compute_lbp(image)
    lbp_features.append(lbp)

lbp_features = np.array(lbp_features)
num_labels = np.array(num_labels)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(lbp_features, num_labels, test_size=0.3, shuffle=True, stratify=labels)

# Create and fit the scaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train the SVM model
svm_model = SVC(kernel='linear')
svm_model.fit(X_train_scaled, y_train)

# Save the trained SVM model and the scaler to separate files
joblib.dump(svm_model, 'svm_banana_model.pkl')
joblib.dump(scaler, 'scaler_banana.pkl')
print("SVM model and scaler saved to 'svm_banana_model.pkl' and 'scaler_banana.pkl'")

# Load the saved SVM model and the scaler (if needed)
loaded_svm_model = joblib.load('svm_banana_model.pkl')
loaded_scaler = joblib.load('scaler_banana.pkl')
print("SVM model and scaler loaded from 'svm_banana_model.pkl' and 'scaler_banana.pkl'")

# Make predictions on the test set using the loaded model and scaler
X_test_scaled_loaded = loaded_scaler.transform(X_test)
y_pred = loaded_svm_model.predict(X_test_scaled_loaded)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")
