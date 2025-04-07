import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib

df = pd.read_csv("results.csv")

# Simulate fraud labels if not available
if 'IsFraud' not in df.columns:
    df['IsFraud'] = (df['Amount'] > 350).astype(int)

# Encode categorical fields
for col in ['Merchant', 'Category', 'PaymentMethod', 'Location']:
    df[col] = LabelEncoder().fit_transform(df[col])

# Split into features and target
X = df[['Amount', 'Merchant', 'Category', 'PaymentMethod', 'Location']]
y = df['IsFraud']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test)))

joblib.dump(model, "fraud_model.pkl")