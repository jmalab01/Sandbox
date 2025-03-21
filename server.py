from flask import Flask, request, jsonify
import pandas as pd
import os
from werkzeug.utils import secure_filename
from sklearn.impute import SimpleImputer

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process and validate data
        result = validate_and_fix_data(filepath)
        return jsonify(result)

    return jsonify({'error': 'Invalid file type'}), 400

def validate_and_fix_data(filepath):
    try:
        df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        
        # Detect missing values
        missing_values = df.isnull().sum().to_dict()
        
        # Detect duplicate rows
        duplicate_rows = df.duplicated().sum()
        
        # Detect anomalies (e.g., negative amounts where not allowed)
        anomalies = {}
        for column in df.select_dtypes(include=['number']):
            if (df[column] < 0).any():
                anomalies[column] = "Negative values detected"

        # AI Fix: Fill missing values using mean for numerical and most frequent for categorical
        imputer_num = SimpleImputer(strategy='mean')
        imputer_cat = SimpleImputer(strategy='most_frequent')

        for column in df.columns:
            if df[column].isnull().sum() > 0:
                if df[column].dtype == 'object':
                    df[column] = imputer_cat.fit_transform(df[[column]])
                else:
                    df[column] = imputer_num.fit_transform(df[[column]])

        # Remove duplicates
        df = df.drop_duplicates()

        fixed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'fixed_' + os.path.basename(filepath))
        df.to_csv(fixed_filepath, index=False)

        return {
            'status': 'success',
            'message': 'File processed successfully',
            'missing_values': missing_values,
            'duplicate_rows': duplicate_rows,
            'anomalies': anomalies,
            'fixed_file': fixed_filepath
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    app.run(debug=True)
