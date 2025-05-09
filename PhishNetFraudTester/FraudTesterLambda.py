import json
import boto3
import random
import uuid
from decimal import Decimal
import datetime

# Connect to your DynamoDB tables
# Final Code
dynamodb = boto3.resource('dynamodb')
TRANSACTIONS_TABLE = dynamodb.Table("TestTransactions")
TEST_RESULTS_TABLE = dynamodb.Table("TestResults")  # New table to store test results

def lambda_handler(event, context):
    # Generate test data with known fraud status (10 test transactions)
    test_data = generate_test_data(10)
    
    # Test results using your rule-based fraud detection algorithm
    rule_based_results = test_rule_based_algorithm(test_data)
    
    # Store results in DynamoDB for analysis
    store_test_results(rule_based_results)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "rule_based_accuracy": rule_based_results["accuracy"],
            "total_transactions": len(test_data),
            "fraud_transactions": sum(1 for t in test_data if t["IsActualFraud"])
        })
    }

def store_transaction(transaction):
    """Store a single transaction in the TestTransactions table"""
    try:
        TRANSACTIONS_TABLE.put_item(Item=transaction)
        print(f"Stored transaction {transaction['TransactionID']} in Transactions")
    except Exception as e:
        print(f"Error storing transaction {transaction['TransactionID']}: {e}")

def generate_test_data(num_transactions):
    """Generate test transactions with known fraud status"""
    test_data = []
    
    # Merchant risk weights from your actual system
    merchant_fraud_weights = {
        "Amazon": 0.2, "Walmart": 0.15, "Target": 0.2, "Starbucks": 0.1,
        "McDonald's": 0.1, "Best Buy": 0.3, "Apple Store": 0.25, "Gas Station": 0.25,
        "Grocery Store": 0.3, "Restaurant": 0.3, "Hotel": 0.5, "Airline": 0.7,
        "Online Service": 0.55, "Luxury Goods": 0.65, "Electronics Depot": 0.4,
        "Travel Agency": 0.6, "VIP Lounge": 0.7, "Crypto Exchange": 0.75,
        "Fine Jewelry": 0.7, "Designer Apparel": 0.6, "Furniture Gallery": 0.5,
        "High-End Electronics": 0.65, "Digital Subscriptions": 0.35,
        "Streaming Service": 0.3, "Fitness Club": 0.25, "Spa & Wellness": 0.4,
        "Boutique Store": 0.45, "Private Clinic": 0.5, "Ride Share": 0.3,
        "Event Tickets": 0.4, "Car Rental": 0.55, "Tech Startup": 0.5,
        "Generic Marketplace": 0.6
    }
    
    locations = [
        "New York", "Los Angeles", "Chicago", "Miami", "London", "Tokyo", "Dubai",
        "San Francisco", "Boston", "Atlanta", "Dallas", "Houston", "Seattle",
        "Philadelphia", "Phoenix", "San Diego", "Denver", "Austin", "Orlando",
        "Las Vegas", "Charlotte", "Detroit", "Minneapolis", "Tampa", "Portland",
        "Toronto", "Vancouver", "Montreal", "Mexico City", "São Paulo", "Buenos Aires",
        "Paris", "Berlin", "Amsterdam", "Madrid", "Rome", "Barcelona", "Copenhagen",
        "Stockholm", "Oslo", "Helsinki", "Zurich", "Vienna", "Moscow", "Istanbul",
        "Bangkok", "Singapore", "Hong Kong", "Seoul", "Kuala Lumpur", "Jakarta",
        "Beijing", "Shanghai", "Mumbai", "New Delhi", "Cape Town", "Johannesburg",
        "Sydney", "Melbourne", "Brisbane", "Auckland", "Wellington"
    ]

    high_risk_locations = [
        "London", "Tokyo", "Dubai", "Moscow", "Beijing", "Johannesburg",
        "Mexico City", "Buenos Aires", "Istanbul", "Lagos"
    ]

    low_risk_locations = [
        "New York", "Los Angeles", "Chicago", "Miami", "Dallas", "Houston",
        "Atlanta", "San Francisco", "Seattle", "Denver", "Phoenix", "San Diego",
        "Boston", "Minneapolis", "Charlotte", "Philadelphia", "Austin", "Portland",
        "Las Vegas", "Orlando", "Tampa", "Columbus", "Detroit", "Indianapolis",
        "Nashville", "Cleveland", "Kansas City", "Milwaukee", "Raleigh", "Pittsburgh",
        "Cincinnati", "Salt Lake City", "St. Louis", "San Antonio", "Sacramento",
        "Baltimore", "New Orleans", "Omaha", "Oklahoma City", "Louisville", "Richmond"
    ]
    
    # Generate both fraudulent and legitimate transactions
    for i in range(num_transactions):
        
        # Select merchant, location, price based on fraud likelihood
        if is_fraud:
            # Merchants: biased to high risk
            weighted_merchants = sorted(merchant_fraud_weights.items(), key=lambda x: x[1], reverse=True)
            merchant = random.choice(weighted_merchants[:5])[0]

            # Amounts: biased to higher risk ranges
            weighted_amounts = sorted(amount_fraud_weights.items(), key=lambda x: x[1], reverse=True)
            amt_range = random.choice(weighted_amounts[:2])[0]  # top 2 high-risk ranges
            amount = Decimal(str(round(random.uniform(*amt_range), 2)))

            # Locations: biased to high-risk cities
            weighted_locations = sorted(location_fraud_weights.items(), key=lambda x: x[1], reverse=True)
            location = random.choice(weighted_locations[:5])[0]
        else:
            # Merchants: biased to low risk
            weighted_merchants = sorted(merchant_fraud_weights.items(), key=lambda x: x[1])
            merchant = random.choice(weighted_merchants[:5])[0]

            # Amounts: biased to lower-risk ranges
            weighted_amounts = sorted(amount_fraud_weights.items(), key=lambda x: x[1])
            amt_range = random.choice(weighted_amounts[:2])[0]  # bottom 2 low-risk ranges
            amount = Decimal(str(round(random.uniform(*amt_range), 2)))

            # Locations: biased to low-risk cities
            weighted_locations = sorted(location_fraud_weights.items(), key=lambda x: x[1])
            location = random.choice(weighted_locations[:5])[0]
        
        transaction = {
            'TransactionID': f"test_txn_{uuid.uuid4().hex[:10]}",
            'UserID': f"test_user_{i}",
            'Amount': amount,
            'Timestamp': datetime.datetime.now().isoformat(),
            'Merchant': merchant,
            'Category': random.choice(["Shopping", "Food", "Travel", "Entertainment", "Utilities", "Other"]),
            'PaymentMethod': random.choice(["Credit Card", "Debit Card", "Mobile Payment", "Online"]),
            'Location': location,
            'RiskScore': Decimal(str(merchant_fraud_weights[merchant])),
            'Status': "Pending",
            'IsActualFraud': is_fraud  # Ground truth for testing
        }
        
        # Store the synthetic transaction in the TestTransactions table
        store_transaction(transaction)
        
        test_data.append(transaction)
    
    return test_data

def test_rule_based_algorithm(test_data):
    """Test rule-based fraud detection algorithm"""
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0
    
    for transaction in test_data:
        amount = transaction['Amount']
        location = transaction['Location']
        risk_score = float(transaction['RiskScore'])  # Convert Decimal to float for calculation
        
        # Calculate fraud score using your rule-based approach
        location_risk = 30 if location in ["Dubai", "Tokyo", "London"] else 0
        
        amount_float = float(amount)
        amount_risk = 40 if amount_float > 500 else (20 if amount_float > 100 else 0)
        fraud_score = (risk_score * 100) + amount_risk + location_risk
        
        # Determine if transaction is flagged as fraud
        is_flagged_fraud = fraud_score > 80
        is_actual_fraud = transaction['IsActualFraud']
        
        # Update counters
        if is_flagged_fraud and is_actual_fraud:
            true_positives += 1
        elif is_flagged_fraud and not is_actual_fraud:
            false_positives += 1
        elif not is_flagged_fraud and not is_actual_fraud:
            true_negatives += 1
        elif not is_flagged_fraud and is_actual_fraud:
            false_negatives += 1
    
    # Calculate performance metrics
    total = len(test_data)
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "algorithm": "rule_based",
        "accuracy": accuracy * 100,
        "precision": precision * 100,
        "recall": recall * 100,
        "f1_score": f1_score * 100,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
        "timestamp": datetime.datetime.now().isoformat()
    }

def store_test_results(results):
    """Store test results in DynamoDB"""
    try:
        TEST_RESULTS_TABLE.put_item(Item={
            'TestID': f"test_{uuid.uuid4().hex[:8]}",
            'Timestamp': results['timestamp'],
            'Algorithm': results['algorithm'],
            'Accuracy': Decimal(str(results['accuracy'])),
            'Precision': Decimal(str(results['precision'])),
            'Recall': Decimal(str(results['recall'])),
            'F1Score': Decimal(str(results['f1_score'])),
            'TruePositives': results['true_positives'],
            'FalsePositives': results['false_positives'],
            'TrueNegatives': results['true_negatives'],
            'FalseNegatives': results['false_negatives']
        })
        print("Test results stored in DynamoDB")
    except Exception as e:
        print(f"Error storing test results: {e}")