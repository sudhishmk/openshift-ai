from flask import Flask, render_template, request, redirect, url_for
import os
import numpy as np
from PIL import Image
import json
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16MB upload

# Load ImageNet class index
def load_class_index():
    with open('imagenet_class_index.json') as f:
        return json.load(f)

# Function to preprocess the uploaded image
def preprocess_image(image_path):
    image = Image.open(image_path).resize((224, 224))
    image_array = np.array(image) / 255.0
    image_array = np.expand_dims(image_array, axis=0)
    return image_array

# Function to make an inference request to OpenVINO endpoint
def predict(image_array, inference_url):
    payload = {
        "inputs": [
            {
                "name": "input",
                "shape": [1, 224, 224, 3],
                "datatype": "FP32",
                "data": image_array.astype(np.float32).tolist()
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(inference_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        # Save the uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Preprocess the image
        image_array = preprocess_image(file_path)
        
        # OpenVINO inference URL
        inference_url = 'https://test-nageshrathodiot-dev.apps.sandbox-m2.ll9k.p1.openshiftapps.com/v2/models/test/infer'

        # Get predictions
        output_prediction = predict(image_array, inference_url)
        
        if output_prediction:
            # Load class index
            class_idx = load_class_index()
            
            # Extract prediction data
            predictions = output_prediction['outputs'][0]['data']
            predictions_np = np.array(predictions)
            
            # Get the predicted class
            max_index = np.argmax(predictions_np)
            label = class_idx[str(max_index)][1]
            
            # Return the result to the index page
            return render_template('index.html', label=label, image_url=url_for('static', filename=f'uploads/{file.filename}'))
        else:
            return render_template('index.html', label="Prediction failed.", image_url=None)
    
    return render_template('index.html', label=None, image_url=None)

# if __name__ == "__main__":
#     app.run(debug=False, port=5050, use_reloader=False, use_debugger=False)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

