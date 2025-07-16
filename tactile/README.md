##  Repository Structure
<pre><code>tactile/
├── arduino_code/
│   └── arduino_collectForceData.ino         # Arduino script for sensor data collection
│
├── model_training/
│
├── feature_extraction.m                     # MATLAB: feature extraction from trials
├── force_dataCollection.py                  # Python: data recording and live plotting
├── trial_data_creation.m                    # MATLAB: create separated trial data from raw datasets
│
├── Separated_Trials/                        # raw datasets divided into single grasp trials
│   └── raw datasets/                        # CSVs of labeled trial data (by material & time)
│
├── test/
│   ├── test_prediction_model.py             # Script to test predictions on sample data
│   └── simulated_data1.csv                  # Example data for model testing
│
├── LivePlot_prediction.py                   # used to live plot sensor data
├── lda_model.joblib                         # trained LDA model
├── material_prediction_model.py             # main script for live force data streaming and model prediction
└── README.md                                # (This file)
</code></pre>



## Instructions for using trained model

1. Upload Arduino Code (Arduino IDE)  
   Flash [`arduino_code/arduino_collectForceData.ino`](arduino_code/arduino_collectForceData.ino) to your Arduino to begin force sensor data collection.

2. Run Live Predictions (Python)  
   Run [`material_prediction_model.py`](material_prediction_model.py) to start live force data streaming and material classification using the LDA model.



## Instructions for collecting data and training model

1. Upload Arduino Code (Arduino IDE)  
   Flash [`arduino_code/arduino_collectForceData.ino`](arduino_code/arduino_collectForceData.ino) to your Arduino to begin force sensor data collection.

2. Collect and Save Sensor Data (Python)  
   Run [`force_dataCollection.py`](force_dataCollection.py) to collect force data via serial from the Arduino. Data will be saved as labeled CSVs in [`Separated_Trials/raw datasets/`](Separated_Trials/raw%20datasets/).

3. Segment Data into Trials (MATLAB)  
   Use [`trial_data_creation.m`](trial_data_creation.m) to divide the raw datasets into single grasp trials. The output will be stored in [`Separated_Trials/`](Separated_Trials/).

4. Extract Features from Trials (MATLAB)  
   Run [`feature_extraction.m`](feature_extraction.m) to compute features from the segmented trials (e.g., mean/max force, duration) for use in model training.

5. Train Model (Python)  
   Train a classifier (e.g., LDA) using features from MATLAB. A trained model is already provided as [`lda_model.joblib`](lda_model.joblib).  
   This code is currently commented out but can load a saved feature vector from MATLAB.

6. Test Model (Python)  
   Use [`test/test_prediction_model.py`](test/test_prediction_model.py) with sample data (e.g., [`test/simulated_data1.csv`](test/simulated_data1.csv)) to validate the trained model.

7. Run Live Predictions (Python)  
   Run [`material_prediction_model.py`](material_prediction_model.py) to start live force data streaming and material classification using the LDA model.


