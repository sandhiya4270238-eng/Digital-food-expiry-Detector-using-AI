# Digital Food Expiry Detector

An AI-based application that detects whether fruits or vegetables are fresh, slightly spoiled, or rotten using image processing and deep learning (TensorFlow/Keras). It includes a Flask web app for easy local usage.

## Features
- **Deep Learning Model:** CNN-based image classification using TensorFlow.
- **Web Dashboard:** Simple and intuitive Flask interface with HTML templates.
- **Image Processing:** OpenCV for resizing and normalization.
- **Recommendations:** Provides actionable advice based on freshness score.

## Folder Structure
```
 digital_food_expiry_detector/
 ├─ app.py                     # Flask Web UI
 ├─ train_model.py             # Script to train the CNN model
 ├─ predict.py                 # CLI prediction script
 ├─ requirements.txt           # Python dependencies
 ├─ README.md                  # This file
 ├─ dataset/                   # Place your raw images here (in Fresh, Slightly Spoiled, Rotten subfolders)
 ├─ templates/                 # HTML templates
 │   └─ index.html
 ├─ models/                    # Saved model weights
 ├─ utils/
 │   ├─ preprocessing.py       # Image resizing & normalization
 │   └─ model_utils.py         # CNN architecture definition
 └─ examples/                  # Example test images
```

## Setup Instructions

1. **Clone or Download the Project**

2. **Create a Virtual Environment (Optional but recommended)**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Prepare Dataset (For Training)**
Place your dataset inside the `dataset` folder as follows:
```
dataset/
 ├─ Fresh/
 ├─ Slightly Spoiled/
 └─ Rotten/
```
*(You can use a public fruit freshness dataset from Kaggle)*

5. **Train the Model**
```bash
python train_model.py
```
This will train the CNN, save a training plot `training_plot.png`, and save the model to `models/model.keras`.

6. **Run the Dashboard**
```bash
python app.py
```
This will start the local Flask server. Open the displayed URL (`http://127.0.0.1:5000/`) in your browser. Upload an image to see the prediction!

## Example Usage (CLI)
If you prefer running a single prediction from the command line:
```bash
python predict.py --image path/to/image.jpg
```
