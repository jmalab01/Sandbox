from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import os
from werkzeug.utils import secure_filename
import hashlib
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Allowed file types
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if file type is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to validate required columns
def validate_columns(df, required_columns):
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, {"error": f"Missing required columns: {', '.join(missing_columns)}"}
    return True, {}

# Function to detect anomalies and ensure all details are included
def detect_anomalies(df):
    anomalies = []
    required_columns = ['Transaction ID', 'Amount']
    valid, message = validate_columns(df, required_columns)
    if not valid:
        return [message]

    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.where(pd.notna(df), None)  # Replace NaN values with None for JSON compatibility

    q1 = df['Amount'].quantile(0.25)
    q3 = df['Amount'].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    std_dev = df['Amount'].std()
    mean_value = df['Amount'].mean()
    threshold = 3 * std_dev

    for index, row in df.iterrows():
        anomaly_details = {
            "row_index": int(index),  # Convert index to int
            "data": row.to_dict()  # Ensure full row data is returned
        }

        if row['Amount'] is None:
            anomaly_details["reason"] = "Missing amount value"
            anomalies.append(anomaly_details)
        elif row['Amount'] < lower_bound or row['Amount'] > upper_bound:
            anomaly_details["reason"] = f"Amount {row['Amount']} is outside expected range ({lower_bound:.2f} - {upper_bound:.2f})"
            anomalies.append(anomaly_details)
        elif abs(row['Amount'] - mean_value) > threshold:
            anomaly_details["reason"] = "Amount deviates significantly from the average (Std Dev method)"
            anomalies.append(anomaly_details)

        if not isinstance(row.get('Transaction ID', None), (int, str)):
            anomaly_details["reason"] = "Transaction ID is not a valid format"
            anomalies.append(anomaly_details)
        if not isinstance(row.get('Date', None), str):
            anomaly_details["reason"] = "Date format is incorrect"
            anomalies.append(anomaly_details)
        if not isinstance(row.get('Category', None), str):
            anomaly_details["reason"] = "Category is in the wrong column or missing"
            anomalies.append(anomaly_details)

    if 'Transaction ID' in df.columns:
        duplicate_transactions = df[df.duplicated(['Transaction ID'], keep=False)]
        for index, row in duplicate_transactions.iterrows():
            anomalies.append({
                "row_index": int(index),
                "reason": "Duplicate transaction detected",
                "data": row.to_dict()
            })

    return anomalies

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            elif filename.endswith('.json'):
                df = pd.read_json(filepath)
            else:
                return jsonify({'error': 'Unsupported file format'}), 400
        except Exception as e:
            logging.error(f"File processing error: {e}")
            return jsonify({'error': 'Error processing file', 'details': str(e)}), 400
        
        anomalies = detect_anomalies(df)
        response = {
            'status': 'File processed',
            'anomalies_found': len(anomalies),
            'anomalies': anomalies
        }
        return jsonify(response)
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)
