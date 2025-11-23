"""
Train the sonar classification model
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os

def load_dataset(data_path='data/sonar_data.csv'):
    """Load and prepare the sonar dataset"""
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        print("Generating synthetic dataset...")
    
        from generate_dataset import SyntheticSonarGenerator
        generator = SyntheticSonarGenerator()
        df = generator.generate_dataset(n_samples_per_class=50, output_path=data_path)
        
        X = df.drop('label', axis=1)
        y = df['label']
        return X, y
    
    print(f"Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)
    X = df.drop('label', axis=1)
    y = df['label']
    return X, y

def train_model(X_train, y_train):
    """Train a Random Forest classifier for multi-class sonar object detection"""
    print("\nTraining Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    print("Training complete!")
    return model

def evaluate_model(model, X_test, y_test):
    print("\nEvaluating model...")
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    print(f"\n{'='*60}")
    print(f"Model Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"{'='*60}\n")
    
    print("Classification Report:")
    print(classification_report(y_test, predictions))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, predictions)
    classes = sorted(list(set(y_test)))
    
    print("\n" + " " * 12 + "  ".join([f"{cls[:8]:>8}" for cls in classes]))
    for i, cls in enumerate(classes):
        print(f"{cls[:10]:>10}  " + "  ".join([f"{cm[i][j]:>8}" for j in range(len(classes))]))
    
    return accuracy

def save_model(model, model_path='model.joblib'):
    """Save the trained model"""
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")

def main():
    print("=" * 60)
    print(" SonarSense")
    print("=" * 60)
    print("\n Model Training Pipeline\n")
    

    X, y = load_dataset()
    
    if X is None:
        print(" Failed to load dataset")
        return
    
    print(f"\nDataset loaded successfully:")
    print(f" Total samples: {X.shape[0]}")
    print(f"  Features: {X.shape[1]}")
    print(f"  Classes: {sorted(list(set(y)))}")
    print(f"  Class distribution:")
    for class_name in sorted(list(set(y))):
        count = sum(y == class_name)
        print(f"     - {class_name}: {count} samples")
    
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Data split:")
    print(f"  Training set: {X_train.shape[0]} samples")
    print(f"  Test set: {X_test.shape[0]} samples")
    
    model = train_model(X_train, y_train)
    
    
    accuracy = evaluate_model(model, X_test, y_test)
    
    
    save_model(model)
    
    
    if hasattr(model, 'feature_importances_'):
        print("\nTop 10 Most Important Features:")
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]
        for i, idx in enumerate(indices, 1):
            print(f"  {i:2d}. Feature {idx:3d}: {importances[idx]:.4f}")
    
    print("\nReady to deploy! Start the API server with: python app.py\n")

if __name__ == "__main__":
    main()