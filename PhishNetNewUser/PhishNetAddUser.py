import json
import boto3
import random
import uuid
from decimal import Decimal
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')

# Set DynamoDB Table
DYNAMODB_TABLE = dynamodb.Table("Users")

def lambda_handler(event, context):

    # Generate a user
    user_data = generate_user(event)

    # Store transaction in DynamoDB
    upload_to_dynamodb(user_data)

    print(f"User ID {user_data['User_ID']} sent to SQS")

    return {"statusCode": 200, "body": "Works!"}

def generate_user(event):
    """Generate a single realistic transaction"""
    # Generate a unique user ID
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    first_name = event['First_Name']
    last_name = event['Last_Name']
    email = event['Email']
    phone = event['Phone_Number']
    location = event['Location']
    
    # Create the transaction with all fields
    user = {
        'User_ID': user_id,
        'First_Name': first_name,
        'Last_Name': last_name, 
        'Email': email,
        'Phone_Number': phone,
        'Created_at': datetime.now().isoformat(),
        'Location': location,
        'Travel Mode': False,  # Automatically disabled
        'Status': "Active"
    }
    print(f"DEBUG: User {user} generated")
    
    return user

def upload_to_dynamodb(user_data):
    """Upload User to DynamoDB"""
    try:
        DYNAMODB_TABLE.put_item(Item=user_data)
        print(f"User {user_data['User_ID']} stored in DynamoDB")
    except Exception as e:
        print(f"Error uploading user to DynamoDB: {e}")
