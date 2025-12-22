#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid
import subprocess

class DebugRefundTest:
    def __init__(self, base_url="https://splitwise-alt.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.test_user_id = None

    def create_test_user_session(self):
        """Create test user and session"""
        print("🔍 Creating Test User and Session...")
        
        try:
            timestamp = int(datetime.now().timestamp())
            self.test_user_id = f"test-user-{timestamp}"
            self.session_token = f"test_session_{timestamp}"
            test_email = f"test.user.{timestamp}@example.com"
            
            user_cmd = f"""mongosh --eval "
                use('test_database');
                var userId = '{self.test_user_id}';
                var sessionToken = '{self.session_token}';
                db.users.insertOne({{
                  user_id: userId,
                  email: '{test_email}',
                  name: 'Test User A',
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
            
            if result.returncode == 0 and "Created user:" in result.stdout:
                print(f"✅ Created user: {self.test_user_id}")
                return True
            else:
                print(f"❌ Failed to create user: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error creating user: {str(e)}")
        
        return False

    def create_test_member(self, name, email):
        """Create a test member and return user_id"""
        try:
            timestamp = int(datetime.now().timestamp())
            user_id = f"test-member-{timestamp}-{name.lower().replace(' ', '')}"
            
            user_cmd = f"""mongosh --eval "
                use('test_database');
                var userId = '{user_id}';
                db.users.insertOne({{
                  user_id: userId,
                  email: '{email}',
                  name: '{name}',
                  picture: 'https://via.placeholder.com/150',
                  default_currency: 'USD',
                  created_at: new Date()
                }});
                print('Created member: ' + userId);
            " """
            
            result = subprocess.run(user_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and "Created member:" in result.stdout:
                print(f"✅ Created member: {user_id}")
                return user_id
            else:
                print(f"❌ Failed to create member {name}: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating member {name}: {str(e)}")
            return None

    def debug_refund_calculation(self):
        """Debug the refund calculation step by step"""
        print("\n🔍 Debug Refund Calculation")
        
        if not self.session_token:
            print("❌ No session token")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create member B
            member_b_id = self.create_test_member("User B", f"userb.{int(datetime.now().timestamp())}@example.com")
            if not member_b_id:
                print("❌ Failed to create member B")
                return False
            
            # Create trip
            trip_data = {
                "name": "Debug Refund Test",
                "description": "Debugging refund calculation",
                "currency": "INR"
            }
            
            print("📝 Creating trip...")
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create trip: {response.status_code}")
                return False
            
            trip_id = response.json().get('trip_id')
            print(f"✅ Created trip: {trip_id}")
            
            # Add member B to trip
            member_data = {"email": f"userb.{int(datetime.now().timestamp())}@example.com", "name": "User B"}
            print("📝 Adding member B to trip...")
            response = requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to add member: {response.status_code}")
                return False
            print("✅ Added member B to trip")
            
            # Verify trip members
            print("\n📊 Trip members:")
            response = requests.get(f"{self.api_url}/trips/{trip_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                for member in trip.get('members', []):
                    print(f"  {member['name']} ({member['user_id']})")
            
            # Create expense: A pays 3000, split equally between A & B (1500 each)
            expense_data = {
                "trip_id": trip_id,
                "description": "Debug Expense - A pays 3000",
                "total_amount": 3000.00,
                "currency": "INR",
                "payers": [{"user_id": self.test_user_id, "amount": 3000.00}],  # A pays 3000
                "splits": [
                    {"user_id": self.test_user_id, "amount": 1500.00},  # A owes 1500
                    {"user_id": member_b_id, "amount": 1500.00}         # B owes 1500
                ]
            }
            
            print("\n📝 Creating expense...")
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create expense: {response.status_code}")
                return False
            
            expense_id = response.json().get('expense_id')
            print(f"✅ Created expense: {expense_id}")
            
            # Check balances BEFORE refund
            print("\n📊 Balances BEFORE refund:")
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code == 200:
                balances = response.json()
                print(f"Raw response: {json.dumps(balances, indent=2)}")
                for balance in balances:
                    print(f"  {balance['name']} ({balance['user_id']}): {balance['balance']}")
            
            # Create refund: 1000 to B
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Debug refund 1000 to B",
                "refunded_to": [member_b_id]
            }
            
            print("\n📝 Creating refund...")
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create refund: {response.status_code}")
                return False
            
            refund_id = response.json().get('refund_id')
            print(f"✅ Created refund: {refund_id}")
            
            # Check balances AFTER refund
            print("\n📊 Balances AFTER refund:")
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code == 200:
                balances = response.json()
                print(f"Raw response: {json.dumps(balances, indent=2)}")
                for balance in balances:
                    print(f"  {balance['name']} ({balance['user_id']}): {balance['balance']}")
            else:
                print(f"❌ Failed to get balances: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Check expense details
            print(f"\n📊 Expense details:")
            response = requests.get(f"{self.api_url}/expenses/{expense_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                expense = response.json()
                print(f"  Total amount: {expense.get('total_amount')}")
                print(f"  Net amount: {expense.get('net_amount')}")
                print(f"  Payers: {expense.get('payers')}")
                print(f"  Splits: {expense.get('splits')}")
                print(f"  Refunds: {expense.get('refunds')}")
            
            # Check refund details
            print(f"\n📊 Refund details:")
            response = requests.get(f"{self.api_url}/refunds/expense/{expense_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                refunds = response.json()
                print(f"  Refunds: {json.dumps(refunds, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in debug: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteMany({{email: /test\\.user\\.|userb\\./}});
                db.user_sessions.deleteMany({{session_token: /test_session/}});
                db.trips.deleteMany({{name: /Debug Refund Test/}});
                db.expenses.deleteMany({{description: /Debug Expense/}});
                db.refunds.deleteMany({{reason: /Debug refund/}});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Test data cleaned")
            else:
                print(f"❌ Cleanup failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error in cleanup: {str(e)}")

    def run_debug(self):
        """Run the debug test"""
        print("🚀 Starting Debug Refund Calculation Test")
        print(f"🌐 Base URL: {self.base_url}")
        
        success = False
        
        if self.create_test_user_session():
            success = self.debug_refund_calculation()
            self.cleanup_test_data()
        
        return 0 if success else 1

def main():
    tester = DebugRefundTest()
    return tester.run_debug()

if __name__ == "__main__":
    sys.exit(main())