import json
import boto3
import random
import uuid
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource('dynamodb')

# Set DynamoDB Table
DYNAMODB_TABLE = dynamodb.Table("Users")

# Predefined users
USER_LIST = [
    {"First_Name": "Aman", "Last_Name": "Jain", "Phone_Number": "+19495329113"},
    {"First_Name": "Timothy", "Last_Name": "Jayamohan", "Phone_Number": "+17247595753"},
    {"First_Name": "Ethan", "Last_Name": "Yang", "Phone_Number": "+16082363352"},
    {"First_Name": "Summit", "Last_Name": "Koegel", "Phone_Number": "+16086049106"},
    {"First_Name": "Anirudh", "Last_Name": "Dahiya", "Phone_Number": "+16179134549"}
]

# Sample locations
LOCATIONS = ["New York", "Chicago", "Seattle", "San Francisco", "Austin"]

def lambda_handler(event, context):
    for user_info in USER_LIST:
        user_data = generate_user(user_info)
        upload_to_dynamodb(user_data)
        print(f"User {user_data['User_ID']} uploaded.")

    return {"statusCode": 200, "body": "All users uploaded successfully."}

def generate_user(user_info):
    """Generate a user record using fixed names and random details"""
    phone = user_info["Phone_Number"]
    user_id = phone  # Using phone number as the primary key
    email = f"{user_info['First_Name'].lower()}.{user_info['Last_Name'].lower()}{random.randint(100,999)}@example.com"
    location = random.choice(LOCATIONS)

    user = {
        'User_ID': user_id,
        'First_Name': user_info['First_Name'],
        'Last_Name': user_info['Last_Name'], 
        'Email': email,
        'Phone_Number': phone,
        'Created_at': datetime.now().isoformat(),
        'Location': location,
        'TravelMode': False,
        'Status': "Active"
    }
    return user

def upload_to_dynamodb(user_data):
    """Upload User to DynamoDB"""
    try:
        DYNAMODB_TABLE.put_item(Item=user_data)
        print(f"User {user_data['User_ID']} stored in DynamoDB")
    except Exception as e:
        print(f"Error uploading user to DynamoDB: {e}")

