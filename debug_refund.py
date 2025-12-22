#!/usr/bin/env python3

import requests
import subprocess
from datetime import datetime

def debug_scenario_1():
    """Debug why Scenario 1 is failing"""
    
    base_url = "https://splitwise-alt.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create test user and session
    timestamp = int(datetime.now().timestamp())
    test_user_id = f"test-user-{timestamp}"
    session_token = f"test_session_{timestamp}"
    test_email = f"test.user.{timestamp}@example.com"
    
    user_cmd = f"""mongosh --eval "
        use('test_database');
        var userId = '{test_user_id}';
        var sessionToken = '{session_token}';
        db.users.insertOne({{
          user_id: userId,
          email: '{test_email}',
          name: 'Test User',
          picture: 'https://via.placeholder.com/150',
          default_currency: 'USD',
          created_at: new Date()
        }});
        db.user_sessions.insertOne({{
          user_id: userId,
          session_token: sessionToken,
          expires_at: new Date(Date.now() + 7*24*60*60*1000),
          created_at: new Date()
        }});
        print('Created user: ' + userId);
    " """
    
    result = subprocess.run(user_cmd, shell=True, capture_output=True, text=True)
    print(f"User creation result: {result.stdout}")
    
    headers = {
        'Authorization': f'Bearer {session_token}',
        'Content-Type': 'application/json'
    }
    
    # Create test users A and B
    user_a_id = f"user_a_{timestamp}"
    user_b_id = f"user_b_{timestamp}"
    
    users_cmd = f"""mongosh --eval "
        use('test_database');
        db.users.insertMany([
            {{
                user_id: '{user_a_id}',
                email: 'user_a@test.com',
                name: 'User A',
                default_currency: 'USD',
                created_at: new Date()
            }},
            {{
                user_id: '{user_b_id}',
                email: 'user_b@test.com', 
                name: 'User B',
                default_currency: 'USD',
                created_at: new Date()
            }}
        ]);
        print('Created test users A and B');
    " """
    
    subprocess.run(users_cmd, shell=True, capture_output=True, text=True)
    
    # Create trip
    trip_data = {
        "name": "Debug Scenario 1 Trip",
        "description": "A pays 3000, B receives 1000 refund",
        "currency": "USD"
    }
    
    response = requests.post(f"{api_url}/trips", json=trip_data, headers=headers, timeout=10)
    print(f"Create trip response: {response.status_code}")
    if response.status_code == 200:
        trip_id = response.json().get('trip_id')
        print(f"Trip ID: {trip_id}")
        
        # Check trip members before adding B
        response = requests.get(f"{api_url}/trips/{trip_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            trip = response.json()
            print(f"Trip members before adding B: {[m['name'] for m in trip['members']]}")
        
        # Add B as member
        member_data = {"email": "user_b@test.com", "name": "User B"}
        response = requests.post(f"{api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
        print(f"Add member response: {response.status_code}")
        if response.status_code == 200:
            print(f"Add member result: {response.json()}")
        
        # Check trip members after adding B
        response = requests.get(f"{api_url}/trips/{trip_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            trip = response.json()
            print(f"Trip members after adding B: {[m['name'] for m in trip['members']]}")
            print(f"Trip member IDs: {[m['user_id'] for m in trip['members']]}")
        
        # Create expense with correct user IDs from trip members
        trip_member_ids = [m['user_id'] for m in trip['members']]
        if len(trip_member_ids) >= 2:
            actual_user_a = trip_member_ids[0]  # First member (creator)
            actual_user_b = trip_member_ids[1]  # Second member (added)
            
            print(f"Using actual user IDs: A={actual_user_a}, B={actual_user_b}")
            
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense - A pays 3000",
                "total_amount": 3000.00,
                "currency": "USD",
                "payers": [{"user_id": actual_user_a, "amount": 3000.00}],
                "splits": [
                    {"user_id": actual_user_a, "amount": 1500.00},
                    {"user_id": actual_user_b, "amount": 1500.00}
                ]
            }
            
            response = requests.post(f"{api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            print(f"Create expense response: {response.status_code}")
            if response.status_code == 200:
                expense_id = response.json().get('expense_id')
                print(f"Expense ID: {expense_id}")
                
                # Create refund: B receives 1000
                refund_data = {
                    "expense_id": expense_id,
                    "amount": 1000.00,
                    "reason": "Refund to B",
                    "refunded_to": [actual_user_b]
                }
                
                response = requests.post(f"{api_url}/refunds", json=refund_data, headers=headers, timeout=10)
                print(f"Create refund response: {response.status_code}")
                if response.status_code == 200:
                    print(f"Refund created: {response.json()}")
                    
                    # Check balances
                    response = requests.get(f"{api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
                    print(f"Get balances response: {response.status_code}")
                    if response.status_code == 200:
                        balances = response.json()
                        print(f"Balances: {balances}")
                        
                        balance_dict = {b['user_id']: b['balance'] for b in balances}
                        a_balance = balance_dict.get(actual_user_a, 0)
                        b_balance = balance_dict.get(actual_user_b, 0)
                        total_balance = sum(balance_dict.values())
                        
                        print(f"A balance: {a_balance} (expected: 2000)")
                        print(f"B balance: {b_balance} (expected: -2000)")
                        print(f"Total balance: {total_balance} (expected: 0)")
                        
                        # Manual calculation verification
                        print("\n--- Manual Calculation ---")
                        print("A: paid 3000, owes 1000 (2000/2) → +2000")
                        print("B: received 1000 refund, owes 1000 (2000/2) → -1000 - 1000 = -2000")
                        print("Total: 2000 + (-2000) = 0")

if __name__ == "__main__":
    debug_scenario_1()