import json
import boto3
import random
import uuid
from decimal import Decimal
from datetime import datetime

# AWS Clients
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Set SQS Queue URL
SQS_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/842675989308/PhishNetQueue"  # Replace with your actual SQS URL

# Set DynamoDB Table
DYNAMODB_TABLE = dynamodb.Table("Transactions")

def lambda_handler(event, context):
    # Generate a transaction
    transaction_data = generate_transaction()

    # Store transaction in DynamoDB
    upload_to_dynamodb(transaction_data)

    # Send transaction ID to SQS
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps({"TransactionID": transaction_data["TransactionID"]})
    )

    print(f"Transaction ID {transaction_data['TransactionID']} sent to SQS")

    return {"statusCode": 200, "body": "Works!"}

def generate_transaction():
    """Generate a single realistic transaction"""
    # Generate a unique transaction ID
    transaction_id = f"txn_{uuid.uuid4().hex[:10]}"
    
    # Generate a user ID (in a real system, this would be from a database of users)
    user_id = f"user_{uuid.uuid4().hex[:8]}"

    
    # List of possible merchants with weights
    merchant_fraud_weights = {
        "Amazon": 0.2,
        "Walmart": 0.15,
        "Target": 0.2,
        "Starbucks": 0.1,
        "McDonald's": 0.1,
        "Best Buy": 0.3,
        "Apple Store": 0.25,
        "Gas Station": 0.25,
        "Grocery Store": 0.3,
        "Restaurant": 0.3,
        "Hotel": 0.5,
        "Airline": 0.7,
        "Online Service": 0.55
    }

    # Pick a completely random merchant (NO weighting)
    selected_merchant = random.choice(list(merchant_fraud_weights.keys()))
    fraud_risk = merchant_fraud_weights[selected_merchant]

    print("Fraud risk: ", fraud_risk)

    amount = round(random.uniform(10, 500), 2)

    # Is this code necessary for location in generation?
    locations = ["New York", "Los Angeles", "Chicago", "Miami", "London", "Tokyo", "Dubai"]
    location = random.choice(locations)
    
    # Create the transaction with all fields
    transaction = {
        'TransactionID': transaction_id,
        'UserID': user_id,
        'Amount': Decimal(str(amount)), 
        'Timestamp': datetime.now().isoformat(),
        'Merchant': selected_merchant,
        'Category': random.choice(["Shopping", "Food", "Travel", "Entertainment", "Utilities", "Other"]),
        'PaymentMethod': random.choice(["Credit Card", "Debit Card", "Mobile Payment", "Online"]),
        'RiskScore': Decimal(str(fraud_risk)),  # Store fraud weight in DynamoDB
        'Status': "Pending"
    }
    
    return transaction

def upload_to_dynamodb(transaction_data):
    """Upload transaction to DynamoDB"""
    try:
        DYNAMODB_TABLE.put_item(Item=transaction_data)
        print(f"Transaction {transaction_data['TransactionID']} stored in DynamoDB")
    except Exception as e:
        print(f"Error uploading transaction to DynamoDB: {e}")