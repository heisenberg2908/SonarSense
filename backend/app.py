"""
Flask API for SonarSense - Sonar signal classification
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
import joblib
import os
import tempfile
from utils import extract_features, preprocess_audio, get_waveform_data, get_frequency_spectrum
from db import Database
from report_generator import ReportGenerator
from datetime import datetime

app = Flask(__name__)
CORS(app)


MODEL_PATH = 'model.joblib'
model = None

def load_model():
    """Load the trained model"""
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"✓ Model loaded from {MODEL_PATH}")
        if hasattr(model, 'classes_'):
            print(f"  Classes: {model.classes_}")
    else:
        print(f"Model not found at {MODEL_PATH}. Please train the model first.")
        print(f"Run: python train_model.py")


db = Database()
report_gen = ReportGenerator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_classes': model.classes_.tolist() if model and hasattr(model, 'classes_') else [],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Predict sonar signal classification"""
    if model is None:
        return jsonify({
            'error': 'Model not loaded. Please train the model first by running: python train_model.py'
        }), 503
    
    try:
        audio_file = None
        features = None
        waveform_data = None
        frequency_data = None
        user_meta = {}
        
        
        if 'file' in request.files:
            audio_file = request.files['file']
            
            file_bytes = audio_file.read()
            
            features = extract_features(file_bytes)
            
            try:
                time, amplitude = get_waveform_data(file_bytes)
                step = max(1, len(time) // 1000)
                waveform_data = {
                    'time': time[::step].tolist(),
                    'amplitude': amplitude[::step].tolist()
                }
                
                freq, magnitude = get_frequency_spectrum(file_bytes)

                step = max(1, len(freq) // 1000)
                frequency_data = {
                    'frequency': freq[::step].tolist(),
                    'magnitude': magnitude[::step].tolist()
                }
            except Exception as e:
                print(f"Warning: Could not extract visualization data: {e}")
            
            if 'user' in request.form:
                user_meta['user'] = request.form['user']
            if 'notes' in request.form:
                user_meta['notes'] = request.form['notes']
                
        elif request.is_json and 'features' in request.json:
            features = np.array(request.json['features'])
            user_meta = request.json.get('meta', {})
        else:
            return jsonify({'error': 'No audio file or features provided'}), 400
        
        
        features = features.reshape(1, -1)
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0]
        
        
        classes = model.classes_
        probabilities_dict = {str(classes[i]): float(probability[i]) for i in range(len(classes))}
        
        
        result = {
            'prediction': str(prediction),
            'confidence': float(max(probability)),
            'probabilities': probabilities_dict,
            'user_meta': user_meta,
            'waveform_data': waveform_data or {},
            'frequency_data': frequency_data or {},
            'features': features.flatten().tolist(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        result_id = db.save_prediction(result)
        result['result_id'] = result_id
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/result/<int:result_id>', methods=['GET'])
def get_result(result_id):
    """Get a single result by ID"""
    try:
        result = db.get_result(result_id)
        if result is None:
            return jsonify({'error': 'Result not found'}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Get prediction history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = db.get_history(limit=limit)
        return jsonify({
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predictions', methods=['GET'])
def get_predictions():
    """Get all predictions from database"""
    try:
        limit = request.args.get('limit', 100, type=int)
        predictions = db.get_predictions(limit=limit)
        return jsonify({
            'predictions': predictions,
            'count': len(predictions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get prediction statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/report/<int:result_id>', methods=['GET'])
def generate_report(result_id):
    """Generate and download PDF report for a result"""
    try:
        result = db.get_result(result_id)
        if result is None:
            return jsonify({'error': 'Result not found'}), 404
        
        report_path = report_gen.generate_pdf_report(result, result_id)
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=os.path.basename(report_path),
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/report/csv', methods=['GET'])
def export_csv():
    """Export all predictions as CSV"""
    try:
        predictions = db.get_predictions(limit=1000)
        csv_path = report_gen.generate_csv_report(predictions)
        
        return send_file(
            csv_path,
            as_attachment=True,
            download_name=os.path.basename(csv_path),
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/train', methods=['POST'])
def train_model_endpoint():
    """Admin endpoint to retrain the model"""
    try:
        auth_token = request.headers.get('X-Admin-Token')
        if auth_token != os.environ.get('ADMIN_TOKEN', 'admin123'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        from train_model import load_dataset, train_model, evaluate_model, save_model
        from sklearn.model_selection import train_test_split
        
        print("Starting model retraining...")
        
        X, y = load_dataset()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        new_model = train_model(X_train, y_train)
        
        accuracy = evaluate_model(new_model, X_test, y_test)
        
        save_model(new_model)
        
        load_model()
        
        return jsonify({
            'success': True,
            'accuracy': float(accuracy),
            'message': 'Model retrained successfully',
            'classes': new_model.classes_.tolist() if hasattr(new_model, 'classes_') else []
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model/info', methods=['GET'])
def model_info():
    """Get model information"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503
    
    return jsonify({
        'model_type': type(model).__name__,
        'n_features': int(model.n_features_in_) if hasattr(model, 'n_features_in_') else None,
        'n_classes': len(model.classes_) if hasattr(model, 'classes_') else None,
        'classes': model.classes_.tolist() if hasattr(model, 'classes_') else []
    })

if __name__ == '__main__':
    load_model()
    
    app.run(debug=True, host='127.0.0.1', port=5000)