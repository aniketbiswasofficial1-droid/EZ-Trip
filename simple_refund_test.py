#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid
import subprocess

class SimpleRefundTest:
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

    def test_simple_refund_scenario(self):
        """Test the exact scenario from user's request"""
        print("\n🔍 Testing Simple Refund Scenario: A pays 3000, split A&B, refund 1000 to B")
        
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
                "name": "Simple Refund Test",
                "description": "Testing refund calculation",
                "currency": "INR"
            }
            
            print("📝 Creating trip...")
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create trip: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            trip_id = response.json().get('trip_id')
            print(f"✅ Created trip: {trip_id}")
            
            # Add member B to trip
            member_data = {"email": f"userb.{int(datetime.now().timestamp())}@example.com", "name": "User B"}
            print("📝 Adding member B to trip...")
            response = requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to add member: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            print("✅ Added member B to trip")
            
            # Create expense: A pays 3000, split equally between A & B (1500 each)
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense - A pays 3000",
                "total_amount": 3000.00,
                "currency": "INR",
                "payers": [{"user_id": self.test_user_id, "amount": 3000.00}],  # A pays 3000
                "splits": [
                    {"user_id": self.test_user_id, "amount": 1500.00},  # A owes 1500
                    {"user_id": member_b_id, "amount": 1500.00}         # B owes 1500
                ]
            }
            
            print("📝 Creating expense...")
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create expense: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            expense_id = response.json().get('expense_id')
            print(f"✅ Created expense: {expense_id}")
            
            # Check balances BEFORE refund
            print("\n📊 Balances BEFORE refund:")
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code == 200:
                balances = response.json()
                for balance in balances:
                    print(f"  {balance['name']}: {balance['balance']}")
            
            # Create refund: 1000 to B
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Refund 1000 to B",
                "refunded_to": [member_b_id]
            }
            
            print("\n📝 Creating refund...")
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create refund: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            refund_id = response.json().get('refund_id')
            print(f"✅ Created refund: {refund_id}")
            
            # Check balances AFTER refund
            print("\n📊 Balances AFTER refund:")
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to get balances: {response.status_code}")
                return False
            
            balances = response.json()
            a_balance = None
            b_balance = None
            
            for balance in balances:
                print(f"  {balance['name']}: {balance['balance']}")
                if balance['user_id'] == self.test_user_id:
                    a_balance = balance['balance']
                elif balance['user_id'] == member_b_id:
                    b_balance = balance['balance']
            
            # Expected calculation:
            # Original: A pays 3000, A owes 1500, B owes 1500 → A balance = +1500, B balance = -1500
            # After refund: Net expense = 3000 - 1000 = 2000
            # New splits: A owes 1000, B owes 1000 (proportional to original 1500:1500)
            # Final: A balance = 3000 - 1000 = +2000, B balance = 0 - 1000 = -1000
            
            print(f"\n🧮 Expected calculation:")
            print(f"  Net expense: 3000 - 1000 = 2000")
            print(f"  New splits: A owes 1000, B owes 1000")
            print(f"  Expected A balance: 3000 - 1000 = +2000")
            print(f"  Expected B balance: 0 - 1000 = -1000")
            
            print(f"\n📊 Actual results:")
            print(f"  A balance: {a_balance}")
            print(f"  B balance: {b_balance}")
            
            # Check if results match expectations
            success = True
            if abs(a_balance - 2000.00) > 0.01:
                print(f"❌ A balance incorrect. Expected 2000, got {a_balance}")
                success = False
            else:
                print(f"✅ A balance correct: {a_balance}")
            
            if abs(b_balance - (-1000.00)) > 0.01:
                print(f"❌ B balance incorrect. Expected -1000, got {b_balance}")
                success = False
            else:
                print(f"✅ B balance correct: {b_balance}")
            
            # Check total balance
            total_balance = a_balance + b_balance
            if abs(total_balance) > 0.01:
                print(f"❌ Total balance not zero: {total_balance}")
                success = False
            else:
                print(f"✅ Total balance is zero: {total_balance}")
            
            # Check expense details
            print(f"\n📊 Expense details:")
            response = requests.get(f"{self.api_url}/expenses/{expense_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                expense = response.json()
                print(f"  Total amount: {expense.get('total_amount')}")
                print(f"  Net amount: {expense.get('net_amount')}")
                print(f"  Refunds: {len(expense.get('refunds', []))}")
                for refund in expense.get('refunds', []):
                    print(f"    Refund: {refund.get('amount')} to {refund.get('refunded_to')}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error in test: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteMany({{email: /test\\.user\\.|userb\\./}});
                db.user_sessions.deleteMany({{session_token: /test_session/}});
                db.trips.deleteMany({{name: /Simple Refund Test/}});
                db.expenses.deleteMany({{description: /Test Expense/}});
                db.refunds.deleteMany({{reason: /Refund.*to B/}});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Test data cleaned")
            else:
                print(f"❌ Cleanup failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error in cleanup: {str(e)}")

    def run_test(self):
        """Run the simple test"""
        print("🚀 Starting Simple Refund Calculation Test")
        print(f"🌐 Base URL: {self.base_url}")
        
        success = False
        
        if self.create_test_user_session():
            success = self.test_simple_refund_scenario()
            self.cleanup_test_data()
        
        if success:
            print("\n🎉 Test PASSED!")
            return 0
        else:
            print("\n💥 Test FAILED!")
            return 1

def main():
    tester = SimpleRefundTest()
    return tester.run_test()

if __name__ == "__main__":
    sys.exit(main())