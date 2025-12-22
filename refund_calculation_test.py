#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid
import subprocess

class RefundCalculationTester:
    def __init__(self, base_url="https://splitwise-alt.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def create_test_user_session(self):
        """Create test user and session"""
        print("\n🔍 Creating Test User and Session...")
        
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
            
            if result.returncode == 0 and "Created user:" in result.stdout:
                self.log_test("Create Test User & Session", True, f"User ID: {self.test_user_id}")
                return True
            else:
                self.log_test("Create Test User & Session", False, f"Creation failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Create Test User & Session", False, f"Error: {str(e)}")
        
        return False

    def test_specific_refund_scenarios(self):
        """Test the exact scenarios from the review request"""
        print("\n🔍 Testing Specific Refund Calculation Scenarios...")
        
        if not self.session_token:
            print("⚠️ Skipping refund calculation tests - no session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        # Create test users for multi-person scenarios
        user_a_id = f"user_a_{int(datetime.now().timestamp())}"
        user_b_id = f"user_b_{int(datetime.now().timestamp())}"
        user_c_id = f"user_c_{int(datetime.now().timestamp())}"
        
        # Create users in database
        try:
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
                    }},
                    {{
                        user_id: '{user_c_id}',
                        email: 'user_c@test.com',
                        name: 'User C', 
                        default_currency: 'USD',
                        created_at: new Date()
                    }}
                ]);
                print('Created test users');
            " """
            
            subprocess.run(users_cmd, shell=True, capture_output=True, text=True)
            print(f"  Created test users: A={user_a_id}, B={user_b_id}, C={user_c_id}")
            
        except Exception as e:
            print(f"  Error creating test users: {e}")
            return

        # Test Scenario 1: A pays 3000, B receives 1000 refund
        # Expected: A +2000, B -2000 (B pays A 2000)
        print("\n  🧪 Scenario 1: A pays 3000, B receives 1000 refund")
        self.test_scenario_1(headers, user_a_id, user_b_id)
        
        # Test Scenario 2: A pays 3000, A receives 1000 refund  
        # Expected: A +1000, B -1000 (B pays A 1000)
        print("\n  🧪 Scenario 2: A pays 3000, A receives 1000 refund")
        self.test_scenario_2(headers, user_a_id, user_b_id)
        
        # Test Scenario 3: A pays 3000, split among A/B/C, C receives 1000 refund
        # Expected: A +2333.33, B -666.67, C -1666.67, Total: 0
        print("\n  🧪 Scenario 3: A pays 3000, split A/B/C, C receives 1000 refund")
        self.test_scenario_3(headers, user_a_id, user_b_id, user_c_id)

    def test_scenario_1(self, headers, user_a_id, user_b_id):
        """A pays 3000, B receives 1000 refund → Expected: A +2000, B -2000"""
        try:
            # Create trip with A and B
            trip_data = {
                "name": "Scenario 1 Test Trip",
                "description": "A pays 3000, B receives 1000 refund",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1: Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add B as member
            member_data = {"email": "user_b@test.com", "name": "User B"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Get actual trip member IDs
            response = requests.get(f"{self.api_url}/trips/{trip_id}", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1: Get Trip", False, f"Status: {response.status_code}")
                return
            
            trip = response.json()
            trip_members = trip['members']
            actual_user_a = trip_members[0]['user_id']  # Creator
            actual_user_b = trip_members[1]['user_id'] if len(trip_members) > 1 else user_b_id
            
            # Create expense: A pays 3000, split equally between A and B
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
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1: Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: B receives 1000
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Refund to B",
                "refunded_to": [user_b_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1: Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1: Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            balance_dict = {b['user_id']: b['balance'] for b in balances}
            
            a_balance = balance_dict.get(user_a_id, 0)
            b_balance = balance_dict.get(user_b_id, 0)
            total_balance = sum(balance_dict.values())
            
            # Expected: A +2000, B -2000, Total: 0
            expected_a = 2000.00
            expected_b = -2000.00
            
            success = (abs(a_balance - expected_a) < 0.01 and 
                      abs(b_balance - expected_b) < 0.01 and 
                      abs(total_balance) < 0.01)
            
            details = f"A: {a_balance:.2f} (exp: {expected_a}), B: {b_balance:.2f} (exp: {expected_b}), Total: {total_balance:.2f}"
            
            self.log_test("Scenario 1: Balance Calculation", success, details)
            
        except Exception as e:
            self.log_test("Scenario 1: Execution", False, f"Error: {str(e)}")

    def test_scenario_2(self, headers, user_a_id, user_b_id):
        """A pays 3000, A receives 1000 refund → Expected: A +1000, B -1000"""
        try:
            # Create trip with A and B
            trip_data = {
                "name": "Scenario 2 Test Trip",
                "description": "A pays 3000, A receives 1000 refund",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2: Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add B as member
            member_data = {"email": "user_b@test.com", "name": "User B"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense: A pays 3000, split equally between A and B
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense - A pays 3000",
                "total_amount": 3000.00,
                "currency": "USD",
                "payers": [{"user_id": user_a_id, "amount": 3000.00}],
                "splits": [
                    {"user_id": user_a_id, "amount": 1500.00},
                    {"user_id": user_b_id, "amount": 1500.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2: Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: A receives 1000
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Refund to A",
                "refunded_to": [user_a_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2: Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2: Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            balance_dict = {b['user_id']: b['balance'] for b in balances}
            
            a_balance = balance_dict.get(user_a_id, 0)
            b_balance = balance_dict.get(user_b_id, 0)
            total_balance = sum(balance_dict.values())
            
            # Expected: A +1000, B -1000, Total: 0
            expected_a = 1000.00
            expected_b = -1000.00
            
            success = (abs(a_balance - expected_a) < 0.01 and 
                      abs(b_balance - expected_b) < 0.01 and 
                      abs(total_balance) < 0.01)
            
            details = f"A: {a_balance:.2f} (exp: {expected_a}), B: {b_balance:.2f} (exp: {expected_b}), Total: {total_balance:.2f}"
            
            self.log_test("Scenario 2: Balance Calculation", success, details)
            
        except Exception as e:
            self.log_test("Scenario 2: Execution", False, f"Error: {str(e)}")

    def test_scenario_3(self, headers, user_a_id, user_b_id, user_c_id):
        """A pays 3000, split among A/B/C, C receives 1000 refund"""
        try:
            # Create trip with A, B, and C
            trip_data = {
                "name": "Scenario 3 Test Trip",
                "description": "A pays 3000, split A/B/C, C receives 1000 refund",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3: Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add B and C as members
            member_b_data = {"email": "user_b@test.com", "name": "User B"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_b_data, headers=headers, timeout=10)
            
            member_c_data = {"email": "user_c@test.com", "name": "User C"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_c_data, headers=headers, timeout=10)
            
            # Create expense: A pays 3000, split equally among A, B, C (1000 each)
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense - A pays 3000, split 3 ways",
                "total_amount": 3000.00,
                "currency": "USD",
                "payers": [{"user_id": user_a_id, "amount": 3000.00}],
                "splits": [
                    {"user_id": user_a_id, "amount": 1000.00},
                    {"user_id": user_b_id, "amount": 1000.00},
                    {"user_id": user_c_id, "amount": 1000.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3: Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: C receives 1000
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Refund to C",
                "refunded_to": [user_c_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3: Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3: Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            balance_dict = {b['user_id']: b['balance'] for b in balances}
            
            a_balance = balance_dict.get(user_a_id, 0)
            b_balance = balance_dict.get(user_b_id, 0)
            c_balance = balance_dict.get(user_c_id, 0)
            total_balance = sum(balance_dict.values())
            
            # Expected calculation:
            # Net expense: 3000 - 1000 = 2000
            # Split 2000 among 3 people = 666.67 each
            # A: paid 3000, owes 666.67 → +2333.33
            # B: paid 0, owes 666.67 → -666.67
            # C: received 1000, owes 666.67 → -1666.67
            # Total: 0
            
            expected_a = 2333.33
            expected_b = -666.67
            expected_c = -1666.67
            
            success = (abs(a_balance - expected_a) < 0.01 and 
                      abs(b_balance - expected_b) < 0.01 and 
                      abs(c_balance - expected_c) < 0.01 and
                      abs(total_balance) < 0.01)
            
            details = f"A: {a_balance:.2f} (exp: {expected_a}), B: {b_balance:.2f} (exp: {expected_b}), C: {c_balance:.2f} (exp: {expected_c}), Total: {total_balance:.2f}"
            
            self.log_test("Scenario 3: Balance Calculation", success, details)
            
        except Exception as e:
            self.log_test("Scenario 3: Execution", False, f"Error: {str(e)}")

    def test_existing_goa_trip(self):
        """Test the existing GOA trip data"""
        print("\n🔍 Testing Existing GOA Trip Data...")
        
        # Test with existing GOA trip session token
        goa_headers = {
            'Authorization': 'Bearer OVzj8YHuDyeXJwdSt5uqkc9-kgQIHrH0WFHipWueICo',
            'Content-Type': 'application/json'
        }
        
        trip_id = "trip_072802d10446"
        
        try:
            # Get trip balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=goa_headers, timeout=10)
            
            if response.status_code != 200:
                self.log_test("GOA Trip: Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            balance_dict = {b['name']: b['balance'] for b in balances}
            total_balance = sum(b['balance'] for b in balances)
            
            # Expected: Aniket +2250, Ritaban -2250, Total: 0
            # (3000 expense, 1500 refund to Ritaban)
            aniket_balance = balance_dict.get('Aniket', 0)
            ritaban_balance = balance_dict.get('Ritaban', 0)
            
            expected_aniket = 2250.00
            expected_ritaban = -2250.00
            
            success = (abs(aniket_balance - expected_aniket) < 0.01 and 
                      abs(ritaban_balance - expected_ritaban) < 0.01 and 
                      abs(total_balance) < 0.01)
            
            details = f"Aniket: {aniket_balance:.2f} (exp: {expected_aniket}), Ritaban: {ritaban_balance:.2f} (exp: {expected_ritaban}), Total: {total_balance:.2f}"
            
            self.log_test("GOA Trip: Balance Verification", success, details)
            
            # Also test trip detail endpoint
            response = requests.get(f"{self.api_url}/trips/{trip_id}", headers=goa_headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                total_expenses = trip.get('total_expenses', 0)
                # Should be 1500 (3000 - 1500 refund)
                expected_total = 1500.00
                
                success = abs(total_expenses - expected_total) < 0.01
                details = f"Total expenses: {total_expenses:.2f} (exp: {expected_total})"
                
                self.log_test("GOA Trip: Total Expenses", success, details)
            
        except Exception as e:
            self.log_test("GOA Trip: Test Execution", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteMany({{email: /test\\.user\\.|user_[abc]@test\\.com/}});
                db.user_sessions.deleteMany({{session_token: /test_session/}});
                db.trips.deleteMany({{name: /Scenario.*Test Trip/}});
                db.expenses.deleteMany({{description: /Test Expense/}});
                db.refunds.deleteMany({{reason: /Refund to [ABC]/}});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_test("Cleanup Test Data", True, "Test data cleaned")
            else:
                self.log_test("Cleanup Test Data", False, f"Cleanup failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Cleanup Test Data", False, f"Error: {str(e)}")

    def run_refund_tests(self):
        """Run all refund calculation tests"""
        print("🚀 Starting Refund Calculation Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        
        # Test existing GOA trip first (no auth setup needed)
        self.test_existing_goa_trip()
        
        # Create test user and session for new scenarios
        if self.create_test_user_session():
            # Test specific scenarios
            self.test_specific_refund_scenarios()
            
            # Cleanup
            self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Refund Calculation Test Summary:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

def main():
    tester = RefundCalculationTester()
    results = tester.run_refund_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())