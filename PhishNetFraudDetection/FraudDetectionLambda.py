import json
import boto3
import os
import joblib
import numpy as np
from decimal import Decimal
from twilio.rest import Client
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Set DynamoDB Tables and SNS Topic ARN
DYNAMODB_TABLE = dynamodb.Table("Transactions")
users_table = dynamodb.Table("Users")
TRANSACTION_MAP_TABLE = dynamodb.Table("UserFraudTransactionsMap")
SNS_TOPIC_ARN = "arn:aws:sns:us-east-2:842675989308:PhishNetAlerts"

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM')
TWILIO_TO_NUMBER = '+19495329113'
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

EMAIL_RECIPIENT1 = "aman.jain030704@gmail.com"

def lambda_handler(event, context):
    print("*** STARTING LAMBDA EXECUTION ***")
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

        print(f"Processing Transaction: {transaction_id}")
        response = DYNAMODB_TABLE.get_item(Key={'TransactionID': transaction_id})
        if 'Item' not in response:
            print(f"Transaction {transaction_id} not found.")
            continue

        transaction = response['Item']
        amount = float(transaction['Amount'])
        fraud_risk = float(transaction.get('RiskScore', 0))
        location = transaction.get('Location', 'Unknown')
        user_id = transaction.get('UserID', 'Unknown')

        # Load user travel mode info
        try:
            user_response = users_table.get_item(Key={'UserID': user_id})
            user_info = user_response.get('Item', {})
            travel_mode = user_info.get('TravelMode', False)
            trusted_locations = user_info.get('TrustedLocation', [])
        except Exception as e:
            print(f"Error fetching user info for {user_id}: {e}")
            travel_mode = False
            trusted_locations = []

        # Location & Amount Risk
        location_risk_score = check_location_risk(location, travel_mode, trusted_locations)
        amount_risk_score = check_amount_risk(amount)

        # Model prediction
        model = joblib.load('/opt/fraud_model.pkl')
        label_encoders = {
            "Merchant": joblib.load('/opt/le_merchant.pkl'),
            "Category": joblib.load('/opt/le_category.pkl'),
            "PaymentMethod": joblib.load('/opt/le_payment.pkl'),
            "Location": joblib.load('/opt/le_location.pkl'),
        }

        flagged_as_fraud = predict_fraud(transaction, model, label_encoders)

        # Add rule-based risk logic to fraud_score if desired
        fraud_score = (fraud_risk * 100) + amount_risk_score + location_risk_score
        print(f"Transaction {transaction_id} fraud score: {fraud_score}")

        fraud_threshold = 50
        if fraud_score > fraud_threshold:
            flagged_as_fraud = True

        if flagged_as_fraud:
            print(f"🚩 Fraud detected for {transaction_id}, ${amount}, {location}")
            update_transaction_status(transaction_id, "Sent to User")
            send_fraud_alert(transaction_id, amount, user_id)

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
        pred = model.predict([encoded])
        return pred[0] == 1
    except Exception as e:
        print(f"Model prediction error: {e}")
        return False

def update_transaction_status(transaction_id, status):
    try:
        DYNAMODB_TABLE.update_item(
            Key={'TransactionID': transaction_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={":status": status}
        )
        print(f"✅ Updated transaction {transaction_id} status to {status}")
    except Exception as e:
        print(f"❌ Error updating status: {e}")

def send_fraud_alert(transaction_id, amount, user_id):
    alert_message = (
        f"🚨 Fraud Alert 🚨\n"
        f"Transaction ID: {transaction_id}\n"
        f"Amount: ${amount}\n"
        f"User: {user_id}\n"
        f"Action is required to verify this transaction."
    )

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=alert_message,
            Subject="Fraud Alert Notification"
        )
        print(f"📧 Email alert sent to {EMAIL_RECIPIENT1}")
    except Exception as e:
        print(f"❌ Error sending SNS email: {e}")

    try:
        sms_message = twilio_client.messages.create(
            body=alert_message,
            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER
        )
        print(f"📲 SMS sent (SID: {sms_message.sid})")
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")

    try:
        TRANSACTION_MAP_TABLE.put_item(
            Item={
                'PhoneNumber': TWILIO_TO_NUMBER,
                'TransactionID': transaction_id,
                'Timestamp': datetime.utcnow().isoformat(),
                'Status': 'Pending'
            }
        )
        print(f"✅ Mapping stored for {TWILIO_TO_NUMBER} → {transaction_id}")
    except Exception as e:
        print(f"❌ Error storing transaction mapping: {e}")
