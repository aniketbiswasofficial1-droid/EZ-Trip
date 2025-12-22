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
                return user_id
            else:
                print(f"Failed to create member {name}: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error creating member {name}: {str(e)}")
            return None

    def test_scenario_1_user_exact_example(self):
        """Test Scenario 1: User's exact example - A pays 3000, split between A & B, refund 1000 to B"""
        print("\n🔍 Testing Scenario 1: User's Exact Example")
        
        if not self.session_token:
            self.log_test("Scenario 1", False, "No session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create member B
            member_b_id = self.create_test_member("Member B", f"memberb.{int(datetime.now().timestamp())}@example.com")
            if not member_b_id:
                self.log_test("Scenario 1 - Create Member B", False, "Failed to create member B")
                return
            
            # Create trip
            trip_data = {
                "name": "Scenario 1 Test Trip",
                "description": "A pays 3000, split between A & B, refund 1000 to B",
                "currency": "INR"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1 - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add member B to trip
            member_data = {"email": f"memberb.{int(datetime.now().timestamp())}@example.com", "name": "Member B"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense: A pays 3000, split between A & B
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense - A pays 3000",
                "total_amount": 3000.00,
                "currency": "INR",
                "payers": [{"user_id": self.test_user_id, "amount": 3000.00}],  # A pays
                "splits": [
                    {"user_id": self.test_user_id, "amount": 1500.00},  # A owes 1500
                    {"user_id": member_b_id, "amount": 1500.00}         # B owes 1500
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1 - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: 1000 to B
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Refund 1000 to B",
                "refunded_to": [member_b_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1 - Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Test expected results
            # Expected: Net 2000, split 1000 each
            # A: paid 3000, owes 1000 → balance: +2000 ✓
            # B: paid 0, owes 1000 → balance: -1000 ✓
            # B owes A 1000
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 1 - Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            success = True
            details = ""
            
            # Find A and B balances
            a_balance = None
            b_balance = None
            for balance in balances:
                if balance['user_id'] == self.test_user_id:
                    a_balance = balance['balance']
                elif balance['user_id'] == member_b_id:
                    b_balance = balance['balance']
            
            details += f"A balance: {a_balance}, B balance: {b_balance}"
            
            # Check expected values
            if a_balance is None:
                success = False
                details += f" ✗ A balance is None"
            elif abs(a_balance - 2000.00) > 0.01:
                success = False
                details += f" ✗ A expected +2000, got {a_balance}"
            else:
                details += " ✓ A balance correct"
            
            if b_balance is None:
                success = False
                details += f" ✗ B balance is None"
            elif abs(b_balance - (-1000.00)) > 0.01:
                success = False
                details += f" ✗ B expected -1000, got {b_balance}"
            else:
                details += " ✓ B balance correct"
            
            # Check total balance is 0
            if a_balance is not None and b_balance is not None:
                total_balance = sum(b['balance'] for b in balances if b['balance'] is not None)
                if abs(total_balance) > 0.01:
                    success = False
                    details += f" ✗ Total balance not zero: {total_balance}"
                else:
                    details += " ✓ Total balanced"
            else:
                success = False
                details += " ✗ Cannot calculate total balance due to None values"
            
            self.log_test("Scenario 1: User's Exact Example", success, details)
            
        except Exception as e:
            self.log_test("Scenario 1: User's Exact Example", False, f"Error: {str(e)}")

    def test_scenario_2_user_second_example(self):
        """Test Scenario 2: User's second example - Same expense, refund 2000 to B"""
        print("\n🔍 Testing Scenario 2: User's Second Example")
        
        if not self.session_token:
            self.log_test("Scenario 2", False, "No session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create member B
            member_b_id = self.create_test_member("Member B2", f"memberb2.{int(datetime.now().timestamp())}@example.com")
            if not member_b_id:
                self.log_test("Scenario 2 - Create Member B", False, "Failed to create member B")
                return
            
            # Create trip
            trip_data = {
                "name": "Scenario 2 Test Trip",
                "description": "A pays 3000, split between A & B, refund 2000 to B",
                "currency": "INR"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2 - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add member B to trip
            member_data = {"email": f"memberb2.{int(datetime.now().timestamp())}@example.com", "name": "Member B2"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense: A pays 3000, split between A & B
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense - A pays 3000 (Scenario 2)",
                "total_amount": 3000.00,
                "currency": "INR",
                "payers": [{"user_id": self.test_user_id, "amount": 3000.00}],
                "splits": [
                    {"user_id": self.test_user_id, "amount": 1500.00},
                    {"user_id": member_b_id, "amount": 1500.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2 - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: 2000 to B
            refund_data = {
                "expense_id": expense_id,
                "amount": 2000.00,
                "reason": "Refund 2000 to B",
                "refunded_to": [member_b_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2 - Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Expected: Net 1000, split 500 each
            # A: paid 3000, owes 500 → balance: +2500 ✓
            # B: paid 0, owes 500 → balance: -500 ✓
            # B owes A 500
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 2 - Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            success = True
            details = ""
            
            # Find A and B balances
            a_balance = None
            b_balance = None
            for balance in balances:
                if balance['user_id'] == self.test_user_id:
                    a_balance = balance['balance']
                elif balance['user_id'] == member_b_id:
                    b_balance = balance['balance']
            
            details += f"A balance: {a_balance}, B balance: {b_balance}"
            
            # Check expected values
            if a_balance is None:
                success = False
                details += f" ✗ A balance is None"
            elif abs(a_balance - 2500.00) > 0.01:
                success = False
                details += f" ✗ A expected +2500, got {a_balance}"
            else:
                details += " ✓ A balance correct"
            
            if b_balance is None:
                success = False
                details += f" ✗ B balance is None"
            elif abs(b_balance - (-500.00)) > 0.01:
                success = False
                details += f" ✗ B expected -500, got {b_balance}"
            else:
                details += " ✓ B balance correct"
            
            # Check total balance is 0
            if a_balance is not None and b_balance is not None:
                total_balance = sum(b['balance'] for b in balances if b['balance'] is not None)
                if abs(total_balance) > 0.01:
                    success = False
                    details += f" ✗ Total balance not zero: {total_balance}"
                else:
                    details += " ✓ Total balanced"
            else:
                success = False
                details += " ✗ Cannot calculate total balance due to None values"
            
            self.log_test("Scenario 2: User's Second Example", success, details)
            
        except Exception as e:
            self.log_test("Scenario 2: User's Second Example", False, f"Error: {str(e)}")

    def test_scenario_3_multi_member_group(self):
        """Test Scenario 3: Multi-member group - A, B, C, D, E with selective expense"""
        print("\n🔍 Testing Scenario 3: Multi-member Group")
        
        if not self.session_token:
            self.log_test("Scenario 3", False, "No session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create members B, C, D, E
            timestamp = int(datetime.now().timestamp())
            member_b_id = self.create_test_member("Member B3", f"memberb3.{timestamp}@example.com")
            member_c_id = self.create_test_member("Member C3", f"memberc3.{timestamp}@example.com")
            member_d_id = self.create_test_member("Member D3", f"memberd3.{timestamp}@example.com")
            member_e_id = self.create_test_member("Member E3", f"membere3.{timestamp}@example.com")
            
            if not all([member_b_id, member_c_id, member_d_id, member_e_id]):
                self.log_test("Scenario 3 - Create Members", False, "Failed to create all members")
                return
            
            # Create trip
            trip_data = {
                "name": "Scenario 3 Test Trip",
                "description": "Multi-member group with selective expense",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3 - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add all members to trip
            for member_id, name, email in [
                (member_b_id, "Member B3", f"memberb3.{timestamp}@example.com"),
                (member_c_id, "Member C3", f"memberc3.{timestamp}@example.com"),
                (member_d_id, "Member D3", f"memberd3.{timestamp}@example.com"),
                (member_e_id, "Member E3", f"membere3.{timestamp}@example.com")
            ]:
                member_data = {"email": email, "name": name}
                requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense: 5000 paid by A, split among A, B, C (activity they did)
            expense_data = {
                "trip_id": trip_id,
                "description": "Activity expense - A, B, C only",
                "total_amount": 5000.00,
                "currency": "USD",
                "payers": [{"user_id": self.test_user_id, "amount": 5000.00}],  # A pays
                "splits": [
                    {"user_id": self.test_user_id, "amount": 1666.67},  # A owes 1666.67
                    {"user_id": member_b_id, "amount": 1666.67},        # B owes 1666.67
                    {"user_id": member_c_id, "amount": 1666.66}         # C owes 1666.66 (rounding)
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3 - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: 1500 to B
            refund_data = {
                "expense_id": expense_id,
                "amount": 1500.00,
                "reason": "Refund 1500 to B",
                "refunded_to": [member_b_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3 - Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Expected: Net 3500, split 1166.67 each among A, B, C
            # A: paid 5000, owes 1166.67 → balance: +3833.33
            # B: paid 0, owes 1166.67 → balance: -1166.67
            # C: paid 0, owes 1166.66 → balance: -1166.66
            # D & E: not affected, balance: 0
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 3 - Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            success = True
            details = ""
            
            # Find all balances
            balance_map = {}
            for balance in balances:
                balance_map[balance['user_id']] = balance['balance']
            
            a_balance = balance_map.get(self.test_user_id, 0)
            b_balance = balance_map.get(member_b_id, 0)
            c_balance = balance_map.get(member_c_id, 0)
            d_balance = balance_map.get(member_d_id, 0)
            e_balance = balance_map.get(member_e_id, 0)
            
            details += f"A: {a_balance}, B: {b_balance}, C: {c_balance}, D: {d_balance}, E: {e_balance}"
            
            # Check expected values (allowing for rounding)
            if abs(a_balance - 3833.33) > 0.02:
                success = False
                details += f" ✗ A expected ~3833.33, got {a_balance}"
            else:
                details += " ✓ A balance correct"
            
            if abs(b_balance - (-1166.67)) > 0.02:
                success = False
                details += f" ✗ B expected ~-1166.67, got {b_balance}"
            else:
                details += " ✓ B balance correct"
            
            if abs(c_balance - (-1166.66)) > 0.02:
                success = False
                details += f" ✗ C expected ~-1166.66, got {c_balance}"
            else:
                details += " ✓ C balance correct"
            
            # D and E should not be affected
            if abs(d_balance) > 0.01 or abs(e_balance) > 0.01:
                success = False
                details += f" ✗ D or E affected when they shouldn't be"
            else:
                details += " ✓ D & E not affected"
            
            # Check total balance is 0
            total_balance = sum(balance_map.values())
            if abs(total_balance) > 0.01:
                success = False
                details += f" ✗ Total balance not zero: {total_balance}"
            else:
                details += " ✓ Total balanced"
            
            self.log_test("Scenario 3: Multi-member Group", success, details)
            
        except Exception as e:
            self.log_test("Scenario 3: Multi-member Group", False, f"Error: {str(e)}")

    def test_scenario_4_multiple_refunds(self):
        """Test Scenario 4: Multiple refunds - 4000 by A, split A & B, refund 500 to A and 500 to B"""
        print("\n🔍 Testing Scenario 4: Multiple Refunds")
        
        if not self.session_token:
            self.log_test("Scenario 4", False, "No session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create member B
            member_b_id = self.create_test_member("Member B4", f"memberb4.{int(datetime.now().timestamp())}@example.com")
            if not member_b_id:
                self.log_test("Scenario 4 - Create Member B", False, "Failed to create member B")
                return
            
            # Create trip
            trip_data = {
                "name": "Scenario 4 Test Trip",
                "description": "Multiple refunds test",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 4 - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add member B to trip
            member_data = {"email": f"memberb4.{int(datetime.now().timestamp())}@example.com", "name": "Member B4"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense: 4000 paid by A, split A & B
            expense_data = {
                "trip_id": trip_id,
                "description": "Multiple refunds expense",
                "total_amount": 4000.00,
                "currency": "USD",
                "payers": [{"user_id": self.test_user_id, "amount": 4000.00}],
                "splits": [
                    {"user_id": self.test_user_id, "amount": 2000.00},
                    {"user_id": member_b_id, "amount": 2000.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 4 - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund 1: 500 to A
            refund_data_1 = {
                "expense_id": expense_id,
                "amount": 500.00,
                "reason": "Refund 500 to A",
                "refunded_to": [self.test_user_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data_1, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 4 - Create Refund 1", False, f"Status: {response.status_code}")
                return
            
            # Create refund 2: 500 to B
            refund_data_2 = {
                "expense_id": expense_id,
                "amount": 500.00,
                "reason": "Refund 500 to B",
                "refunded_to": [member_b_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data_2, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 4 - Create Refund 2", False, f"Status: {response.status_code}")
                return
            
            # Expected: Net 3000, split 1500 each
            # A: paid 4000, owes 1500 → balance: +2500
            # B: paid 0, owes 1500 → balance: -1500
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Scenario 4 - Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            success = True
            details = ""
            
            # Find A and B balances
            a_balance = None
            b_balance = None
            for balance in balances:
                if balance['user_id'] == self.test_user_id:
                    a_balance = balance['balance']
                elif balance['user_id'] == member_b_id:
                    b_balance = balance['balance']
            
            details += f"A balance: {a_balance}, B balance: {b_balance}"
            
            # Check expected values
            if abs(a_balance - 2500.00) > 0.01:
                success = False
                details += f" ✗ A expected +2500, got {a_balance}"
            else:
                details += " ✓ A balance correct"
            
            if abs(b_balance - (-1500.00)) > 0.01:
                success = False
                details += f" ✗ B expected -1500, got {b_balance}"
            else:
                details += " ✓ B balance correct"
            
            # Check total balance is 0
            total_balance = sum(b['balance'] for b in balances)
            if abs(total_balance) > 0.01:
                success = False
                details += f" ✗ Total balance not zero: {total_balance}"
            else:
                details += " ✓ Total balanced"
            
            self.log_test("Scenario 4: Multiple Refunds", success, details)
            
        except Exception as e:
            self.log_test("Scenario 4: Multiple Refunds", False, f"Error: {str(e)}")

    def test_edge_case_refund_equals_expense(self):
        """Test Edge Case: Refund equals expense (net = 0)"""
        print("\n🔍 Testing Edge Case: Refund Equals Expense")
        
        if not self.session_token:
            self.log_test("Edge Case - Refund Equals Expense", False, "No session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create member B
            member_b_id = self.create_test_member("Member B5", f"memberb5.{int(datetime.now().timestamp())}@example.com")
            if not member_b_id:
                self.log_test("Edge Case - Create Member B", False, "Failed to create member B")
                return
            
            # Create trip
            trip_data = {
                "name": "Edge Case Test Trip",
                "description": "Refund equals expense",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Edge Case - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add member B to trip
            member_data = {"email": f"memberb5.{int(datetime.now().timestamp())}@example.com", "name": "Member B5"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense: 1000 paid by A, split A & B
            expense_data = {
                "trip_id": trip_id,
                "description": "Edge case expense",
                "total_amount": 1000.00,
                "currency": "USD",
                "payers": [{"user_id": self.test_user_id, "amount": 1000.00}],
                "splits": [
                    {"user_id": self.test_user_id, "amount": 500.00},
                    {"user_id": member_b_id, "amount": 500.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Edge Case - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            
            # Create refund: 1000 (equals expense)
            refund_data = {
                "expense_id": expense_id,
                "amount": 1000.00,
                "reason": "Full refund",
                "refunded_to": [member_b_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Edge Case - Create Refund", False, f"Status: {response.status_code}")
                return
            
            # Expected: Net 0, no one owes anything
            # A: paid 1000, owes 0 → balance: +1000
            # B: paid 0, owes 0 → balance: 0
            # Wait, this doesn't seem right. Let me recalculate...
            # If net = 0, then there's nothing to split, so everyone should owe 0
            # A: paid 1000, owes 0 → balance: +1000
            # B: paid 0, owes 0 → balance: 0
            # But this doesn't balance! The issue is that when net = 0, 
            # the expense effectively didn't happen, but A still paid 1000.
            # This is a complex edge case that needs careful handling.
            
            # Check balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Edge Case - Get Balances", False, f"Status: {response.status_code}")
                return
            
            balances = response.json()
            success = True
            details = ""
            
            # Find A and B balances
            a_balance = None
            b_balance = None
            for balance in balances:
                if balance['user_id'] == self.test_user_id:
                    a_balance = balance['balance']
                elif balance['user_id'] == member_b_id:
                    b_balance = balance['balance']
            
            details += f"A balance: {a_balance}, B balance: {b_balance}"
            
            # Check total balance is 0 (most important)
            total_balance = sum(b['balance'] for b in balances)
            if abs(total_balance) > 0.01:
                success = False
                details += f" ✗ Total balance not zero: {total_balance}"
            else:
                details += " ✓ Total balanced"
            
            # For net = 0 case, the exact individual balances depend on implementation
            # The key is that the total should be balanced
            
            self.log_test("Edge Case: Refund Equals Expense", success, details)
            
        except Exception as e:
            self.log_test("Edge Case: Refund Equals Expense", False, f"Error: {str(e)}")

    def test_api_endpoints_consistency(self):
        """Test that all API endpoints return consistent values"""
        print("\n🔍 Testing API Endpoints Consistency")
        
        if not self.session_token:
            self.log_test("API Consistency", False, "No session token")
            return
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create a simple test case
            member_b_id = self.create_test_member("Member B6", f"memberb6.{int(datetime.now().timestamp())}@example.com")
            if not member_b_id:
                self.log_test("API Consistency - Create Member", False, "Failed to create member")
                return
            
            # Create trip
            trip_data = {
                "name": "API Consistency Test",
                "description": "Testing API consistency",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("API Consistency - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add member B
            member_data = {"email": f"memberb6.{int(datetime.now().timestamp())}@example.com", "name": "Member B6"}
            requests.post(f"{self.api_url}/trips/{trip_id}/members", json=member_data, headers=headers, timeout=10)
            
            # Create expense and refund
            expense_data = {
                "trip_id": trip_id,
                "description": "Consistency test expense",
                "total_amount": 1000.00,
                "currency": "USD",
                "payers": [{"user_id": self.test_user_id, "amount": 1000.00}],
                "splits": [
                    {"user_id": self.test_user_id, "amount": 500.00},
                    {"user_id": member_b_id, "amount": 500.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=headers, timeout=10)
            expense_id = response.json().get('expense_id')
            
            refund_data = {
                "expense_id": expense_id,
                "amount": 200.00,
                "reason": "Consistency test refund",
                "refunded_to": [member_b_id]
            }
            
            requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
            
            # Now test all endpoints for consistency
            success = True
            details = ""
            
            # 1. GET /api/trips
            response = requests.get(f"{self.api_url}/trips", headers=headers, timeout=10)
            if response.status_code == 200:
                trips = response.json()
                target_trip = next((t for t in trips if t['trip_id'] == trip_id), None)
                if target_trip:
                    trips_total_expenses = target_trip.get('total_expenses', 0)
                    trips_your_balance = target_trip.get('your_balance', 0)
                    details += f"Trips endpoint - Total: {trips_total_expenses}, Balance: {trips_your_balance}"
                else:
                    success = False
                    details += "Trip not found in trips list"
            else:
                success = False
                details += f"Trips endpoint failed: {response.status_code}"
            
            # 2. GET /api/trips/{trip_id}
            response = requests.get(f"{self.api_url}/trips/{trip_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                trip_total_expenses = trip.get('total_expenses', 0)
                trip_your_balance = trip.get('your_balance', 0)
                details += f" | Trip detail - Total: {trip_total_expenses}, Balance: {trip_your_balance}"
                
                # Check consistency
                if abs(trips_total_expenses - trip_total_expenses) > 0.01:
                    success = False
                    details += " ✗ Total expenses inconsistent"
                if abs(trips_your_balance - trip_your_balance) > 0.01:
                    success = False
                    details += " ✗ Your balance inconsistent"
            else:
                success = False
                details += f" | Trip detail failed: {response.status_code}"
            
            # 3. GET /api/trips/{trip_id}/balances
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
            if response.status_code == 200:
                balances = response.json()
                user_balance_from_balances = next((b['balance'] for b in balances if b['user_id'] == self.test_user_id), 0)
                details += f" | Balances endpoint - User balance: {user_balance_from_balances}"
                
                # Check consistency with trip detail
                if abs(trip_your_balance - user_balance_from_balances) > 0.01:
                    success = False
                    details += " ✗ Balance inconsistent with balances endpoint"
            else:
                success = False
                details += f" | Balances endpoint failed: {response.status_code}"
            
            # 4. GET /api/expenses/trip/{trip_id}
            response = requests.get(f"{self.api_url}/expenses/trip/{trip_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                expenses = response.json()
                total_net_amount = sum(e.get('net_amount', 0) for e in expenses)
                details += f" | Expenses endpoint - Total net: {total_net_amount}"
                
                # Check consistency with trip total
                if abs(trip_total_expenses - total_net_amount) > 0.01:
                    success = False
                    details += " ✗ Total expenses inconsistent with expenses net amount"
            else:
                success = False
                details += f" | Expenses endpoint failed: {response.status_code}"
            
            if success:
                details += " ✓ All endpoints consistent"
            
            self.log_test("API Endpoints Consistency", success, details)
            
        except Exception as e:
            self.log_test("API Endpoints Consistency", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteMany({{email: /test\\.user\\.|memberb|memberc|memberd|membere/}});
                db.user_sessions.deleteMany({{session_token: /test_session/}});
                db.trips.deleteMany({{name: /Scenario|Edge Case|API Consistency/}});
                db.expenses.deleteMany({{description: /Test|Scenario|Edge case|Consistency/}});
                db.refunds.deleteMany({{reason: /Refund|test|Test|Full refund|Consistency/}});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_test("Cleanup Test Data", True, "Test data cleaned")
            else:
                self.log_test("Cleanup Test Data", False, f"Cleanup failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Cleanup Test Data", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all refund calculation tests"""
        print("🚀 Starting Refund Calculation Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        
        # Create test user and session
        if self.create_test_user_session():
            # Test all scenarios
            self.test_scenario_1_user_exact_example()
            self.test_scenario_2_user_second_example()
            self.test_scenario_3_multi_member_group()
            self.test_scenario_4_multiple_refunds()
            self.test_edge_case_refund_equals_expense()
            self.test_api_endpoints_consistency()
            
            # Cleanup
            self.cleanup_test_data()
        
        # Print summary
        print(f"\n📊 Test Summary:")
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
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())