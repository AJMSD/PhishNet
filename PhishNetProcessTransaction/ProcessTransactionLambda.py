import json
import boto3
import random
import uuid
from decimal import Decimal
from datetime import datetime

# AWS Clients
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Set SQS Queue URL and Tables
SQS_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/842675989308/PhishNetQueue"
TRANSACTION_TABLE = dynamodb.Table("Transactions")
USER_TABLE = dynamodb.Table("Users")

def lambda_handler(event, context):
    # Get a user from the Users table
    user_id = get_random_user_id()
    if not user_id:
        return {"statusCode": 500, "body": "No users available in the Users table."}

    # Generate a transaction
    transaction_data = generate_transaction(user_id)

    # Store transaction in DynamoDB
    upload_to_dynamodb(transaction_data)

    # Send transaction ID to SQS
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps({"TransactionID": transaction_data["TransactionID"]})
    )

    print(f"Transaction ID {transaction_data['TransactionID']} sent to SQS")

    return {"statusCode": 200, "body": "Transaction created and sent to SQS"}

def get_random_user_id():
    """Scan the Users table and pick a random user ID (Phone Number)"""
    try:
        response = USER_TABLE.scan(ProjectionExpression="User_ID")
        users = response.get("Items", [])
        if not users:
            print("No users found in Users table.")
            return None
        user_id = random.choice(users)["User_ID"]
        print(f"Selected User ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"Error reading from Users table: {e}")
        return None

def generate_transaction(user_id):
    """Generate a single realistic transaction using an existing user"""
    transaction_id = f"txn_{uuid.uuid4().hex[:10]}"

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

    selected_merchant = random.choice(list(merchant_fraud_weights.keys()))
    fraud_risk = merchant_fraud_weights[selected_merchant]
    amount = round(random.uniform(10, 500), 2)
    location = random.choice(["New York", "Los Angeles", "Chicago", "Miami", "London", "Tokyo", "Dubai"])

    transaction = {
        'TransactionID': transaction_id,
        'UserID': user_id,
        'Amount': Decimal(str(amount)),
        'Timestamp': datetime.now().isoformat(),
        'Merchant': selected_merchant,
        'Category': random.choice(["Shopping", "Food", "Travel", "Entertainment", "Utilities", "Other"]),
        'PaymentMethod': random.choice(["Credit Card", "Debit Card", "Mobile Payment", "Online"]),
        'Location': location,
        'RiskScore': Decimal(str(fraud_risk)),
        'Status': "Pending"
    }

    return transaction

def upload_to_dynamodb(transaction_data):
    """Upload transaction to DynamoDB"""
    try:
        TRANSACTION_TABLE.put_item(Item=transaction_data)
        print(f"Transaction {transaction_data['TransactionID']} stored in DynamoDB")
    except Exception as e:
        print(f"Error uploading transaction to DynamoDB: {e}")
