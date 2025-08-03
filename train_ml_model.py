import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
import os

def train_model():
    """Loads data, trains a classifier, and saves it."""
    # Load the dataset
    df = pd.read_csv('data/applications.csv')

    # Feature Engineering (simple example)
    df['income_per_person'] = df['monthly_income'] / df['family_size']

    # Select features and target
    features = ['age', 'monthly_income', 'family_size', 'employment_years', 'income_per_person']
    target = 'eligibility_status'

    X = df[features]
    y = df[target]

    # Encode the target variable
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    
    # Initialize and train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    # Save the model and the label encoder
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/eligibility_classifier.joblib')
    joblib.dump(le, 'models/label_encoder.joblib')
    joblib.dump(features, 'models/features.joblib') # Save feature order
    
    print("\nModel and encoder saved successfully to 'models/' directory.")

if __name__ == "__main__":
    train_model()