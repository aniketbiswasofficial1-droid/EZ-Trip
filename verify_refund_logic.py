#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid
import subprocess

class VerifyRefundLogic:
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
                  name: 'User A',
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

    def verify_user_scenario_2(self):
        """Verify User's Scenario 2: A pays 3000, refund 2000 to B, expected net 1000"""
        print("\n🔍 Verifying User's Scenario 2")
        print("Expected: A pays 3000, split A&B, refund 2000 to B")
        print("Expected: Net 1000, split 500 each")
        print("Expected: A balance +2500, B balance -500, Total 0")
        
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
                "name": "Verify Scenario 2",
                "description": "Verifying refund calculation",
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
            
            # Create expense: A pays 3000, split equally between A & B (1500 each)
            expense_data = {
                "trip_id": trip_id,
                "description": "Scenario 2 Expense - A pays 3000",
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
                return False
            
            expense_id = response.json().get('expense_id')
            print(f"✅ Created expense: {expense_id}")
            
            # Create refund: 2000 to B
            refund_data = {
                "expense_id": expense_id,
                "amount": 2000.00,
                "reason": "Scenario 2 refund 2000 to B",
                "refunded_to": [member_b_id]
            }
            
            print("📝 Creating refund...")
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to create refund: {response.status_code}")
                return False
            
            refund_id = response.json().get('refund_id')
            print(f"✅ Created refund: {refund_id}")
            
            # Check balances
            print("\n📊 Checking balances...")
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to get balances: {response.status_code}")
                return False
            
            balances = response.json()
            print(f"Raw balances: {json.dumps(balances, indent=2)}")
            
            a_balance = None
            b_balance = None
            
            for balance in balances:
                if balance['user_id'] == self.test_user_id:
                    a_balance = balance['balance']
                elif balance['user_id'] == member_b_id:
                    b_balance = balance['balance']
            
            print(f"\n🧮 Manual calculation:")
            print(f"  Original expense: 3000")
            print(f"  Refund: 2000")
            print(f"  Net expense: 3000 - 2000 = 1000")
            print(f"  Original splits: A=1500, B=1500 (ratio 1:1)")
            print(f"  New splits based on net: A=500, B=500")
            print(f"  A balance: paid 3000 - owes 500 = +2500")
            print(f"  B balance: paid 0 - owes 500 = -500")
            print(f"  Total: 2500 + (-500) = 2000 ❌ Should be 0!")
            
            print(f"\n📊 Actual results:")
            print(f"  A balance: {a_balance}")
            print(f"  B balance: {b_balance}")
            
            if a_balance is not None and b_balance is not None:
                total = a_balance + b_balance
                print(f"  Total: {total}")
                
                if abs(total) < 0.01:
                    print("✅ Total is balanced (close to 0)")
                    return True
                else:
                    print(f"❌ Total is NOT balanced: {total}")
                    print("\n🔍 This suggests there's still an issue with the refund calculation logic!")
                    return False
            else:
                print("❌ One or both balances are None")
                return False
            
        except Exception as e:
            print(f"❌ Error in verification: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteMany({{email: /test\\.user\\.|userb\\./}});
                db.user_sessions.deleteMany({{session_token: /test_session/}});
                db.trips.deleteMany({{name: /Verify Scenario/}});
                db.expenses.deleteMany({{description: /Scenario 2 Expense/}});
                db.refunds.deleteMany({{reason: /Scenario 2 refund/}});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Test data cleaned")
            else:
                print(f"❌ Cleanup failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error in cleanup: {str(e)}")

    def run_verification(self):
        """Run the verification"""
        print("🚀 Starting Refund Logic Verification")
        print(f"🌐 Base URL: {self.base_url}")
        
        success = False
        
        if self.create_test_user_session():
            success = self.verify_user_scenario_2()
            self.cleanup_test_data()
        
        if success:
            print("\n🎉 Verification PASSED - Refund logic is working correctly!")
        else:
            print("\n💥 Verification FAILED - There's still an issue with the refund logic!")
            print("\n🔧 The issue is that the total balance is not zero, indicating double-counting.")
            print("🔧 The current implementation needs to be fixed to properly handle refund recipients.")
        
        return 0 if success else 1

def main():
    verifier = VerifyRefundLogic()
    return verifier.run_verification()

if __name__ == "__main__":
    sys.exit(main())