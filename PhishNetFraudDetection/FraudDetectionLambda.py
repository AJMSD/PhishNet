import json
import boto3
import os
import joblib
from decimal import Decimal
from twilio.rest import Client
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')

# DynamoDB Tables
transactions_table = dynamodb.Table("Transactions")
users_table = dynamodb.Table("Users")
mapping_table = dynamodb.Table("UserFraudTransactionsMap")

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def lambda_handler(event, context):
    print("STARTING LAMBDA EXECUTION")
    print("Received event from SQS:", json.dumps(event))

    for record in event['Records']:
        print("Raw message body:", record['body'])

        try:
            message = json.loads(record['body'])
            if isinstance(message, str):
                message = json.loads(message)
        except json.JSONDecodeError:
            print("ERROR: Failed to decode JSON message:", record['body'])
            return {"statusCode": 400, "body": "Invalid JSON"}

        transaction_id = message.get('TransactionID')
        if not transaction_id:
            print("ERROR: TransactionID is missing!")
            continue

        print(f"Processing transaction: {transaction_id}")
        txn_response = transactions_table.get_item(Key={'TransactionID': transaction_id})

        if 'Item' not in txn_response:
            print(f"Transaction {transaction_id} not found in Transactions table.")
            continue

        transaction = txn_response['Item']
        amount = float(transaction['Amount'])
        fraud_risk = float(transaction.get('RiskScore', 0))
        location = transaction.get('Location', 'Unknown')
        user_id = transaction.get('UserID', 'Unknown')

        try:
            user_response = users_table.get_item(Key={'UserID': user_id})
            user_info = user_response.get('Item', {})
            travel_mode = user_info.get('TravelMode', False)
            trusted_locations = user_info.get('TrustedLocation', [])
            user_phone = user_info.get('Phone_Number')
            if not user_phone:
                print(f"User {user_id} does not have a phone number. Skipping SMS.")
                continue
        except Exception as e:
            print(f"Error fetching user info for {user_id}: {e}")
            continue

        # Rule-based scoring
        location_risk_score = check_location_risk(location, travel_mode, trusted_locations)
        amount_risk_score = check_amount_risk(amount)
        fraud_score = (fraud_risk * 100) + amount_risk_score + location_risk_score
        print(f"Transaction {transaction_id} fraud score: {fraud_score}")

        # ML model prediction
        model = joblib.load('/opt/fraud_model.pkl')
        label_encoders = {
            "Merchant": joblib.load('/opt/le_merchant.pkl'),
            "Category": joblib.load('/opt/le_category.pkl'),
            "PaymentMethod": joblib.load('/opt/le_payment.pkl'),
            "Location": joblib.load('/opt/le_location.pkl'),
        }
        flagged_as_fraud = predict_fraud(transaction, model, label_encoders)

        # Apply hybrid logic
        fraud_threshold = 50
        if fraud_score > fraud_threshold:
            flagged_as_fraud = True

        if flagged_as_fraud:
            print(f"FRAUD DETECTED for transaction {transaction_id}")
            update_transaction_status(transaction_id, "Sent to User")
            send_fraud_alert(transaction_id, amount, user_id, user_phone)

    return {"statusCode": 200, "body": "Processing complete"}

def check_location_risk(location, travel_mode=False, trusted_locations=None):
    high_risk_locations = ["Dubai", "Tokyo", "London"]
    trusted_locations = trusted_locations or []

    if travel_mode and location in trusted_locations:
        print(f"{location} is trusted during travel mode.")
        return 0
    if location in high_risk_locations:
        return 30
    return 0

def check_amount_risk(amount):
    if amount > 3000:
        return 40
    elif amount > 1000:
        return 20
    return 0

def predict_fraud(transaction, model, label_encoders):
    try:
        encoded = [
            float(transaction['Amount']),
            label_encoders["Merchant"].transform([transaction['Merchant']])[0],
            label_encoders["Category"].transform([transaction['Category']])[0],
            label_encoders["PaymentMethod"].transform([transaction['PaymentMethod']])[0],
            label_encoders["Location"].transform([transaction['Location']])[0],
        ]
        prediction = model.predict([encoded])
        return prediction[0] == 1
    except Exception as e:
        print(f"Model prediction error: {e}")
        return False

def update_transaction_status(transaction_id, status):
    try:
        transactions_table.update_item(
            Key={'TransactionID': transaction_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "Status"},
            ExpressionAttributeValues={":val": status}
        )
        print(f"Transaction {transaction_id} status updated to '{status}'")
    except Exception as e:
        print(f"Error updating transaction status: {e}")

def send_fraud_alert(transaction_id, amount, user_id, phone_number):
    merchant = "Unknown"
    location = "Unknown"

    # Fetch transaction details for context
    try:
        txn = transactions_table.get_item(Key={'TransactionID': transaction_id})
        if 'Item' in txn:
            merchant = txn['Item'].get('Merchant', "Unknown")
            location = txn['Item'].get('Location', "Unknown")
    except Exception as e:
        print(f"Warning: Failed to fetch full transaction context: {e}")

    message = (
        f"Fraud Alert: A recent purchase from {merchant} in {location} for ${amount} "
        f"has been flagged as potential fraud in our system. "
        f"Reply YES to confirm if it is fraud, or NO to deny it. Thank you."
    )

    try:
        sms = twilio_client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=phone_number
        )
        print(f"SMS sent to {phone_number} (SID: {sms.sid})")
    except Exception as e:
        print(f"Error sending SMS via Twilio: {e}")

    try:
        mapping_table.put_item(
            Item={
                'PhoneNumber': phone_number,
                'TransactionID': transaction_id,
                'Timestamp': datetime.utcnow().isoformat(),
                'Status': 'Sent to User'
            }
        )
        print(f"Stored mapping for {phone_number} → {transaction_id}")
    except Exception as e:
        print(f"Error storing transaction mapping: {e}")
