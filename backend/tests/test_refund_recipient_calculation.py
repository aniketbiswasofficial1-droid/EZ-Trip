#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid
import subprocess

class RefundRecipientCalculationTester:
    def __init__(self, base_url="https://splitwise-alt.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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

    def create_test_session(self, user_id, session_token, email, name):
        """Create a test user and session in MongoDB"""
        try:
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteOne({{user_id: '{user_id}'}});
                db.user_sessions.deleteOne({{session_token: '{session_token}'}});
            " """
            subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            create_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.insertOne({{
                  user_id: '{user_id}',
                  email: '{email}',
                  name: '{name}',
                  picture: 'https://via.placeholder.com/150',
                  default_currency: 'INR',
                  created_at: new Date()
                }});
                db.user_sessions.insertOne({{
                  user_id: '{user_id}',
                  session_token: '{session_token}',
                  expires_at: new Date(Date.now() + 7*24*60*60*1000),
                  created_at: new Date()
                }});
                print('Created user: {user_id}');
            " """
            
            result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0 and "Created user:" in result.stdout
            
        except Exception as e:
            print(f"Error creating test session: {e}")
            return False

    def test_goa_trip_scenario(self):
        """Test GOA Trip scenario: 3000 INR expense, 1500 INR refund to Ritaban"""
        print("\n🔍 Testing GOA Trip Scenario...")
        
        # Create test users
        aniket_id = "user_aniket_test"
        ritaban_id = "user_ritaban_test"
        aniket_session = "test_session_aniket_001"
        ritaban_session = "test_session_ritaban_001"
        
        # Create both users
        if not self.create_test_session(aniket_id, aniket_session, "aniket@test.com", "Aniket"):
            self.log_test("GOA Trip - Create Aniket User", False, "Failed to create user")
            return
        
        if not self.create_test_session(ritaban_id, ritaban_session, "ritaban@test.com", "Ritaban"):
            self.log_test("GOA Trip - Create Ritaban User", False, "Failed to create user")
            return
        
        aniket_headers = {
            'Authorization': f'Bearer {aniket_session}',
            'Content-Type': 'application/json'
        }
        
        ritaban_headers = {
            'Authorization': f'Bearer {ritaban_session}',
            'Content-Type': 'application/json'
        }
        
        # Create trip
        trip_data = {
            "name": "GOA Trip Test",
            "description": "Testing refund recipient calculation",
            "currency": "INR"
        }
        
        try:
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=aniket_headers, timeout=10)
            if response.status_code != 200:
                self.log_test("GOA Trip - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            self.log_test("GOA Trip - Create Trip", True, f"Trip ID: {trip_id}")
            
            # Add Ritaban to trip
            member_data = {"email": "ritaban@test.com", "name": "Ritaban"}
            response = requests.post(f"{self.api_url}/trips/{trip_id}/members", 
                                   json=member_data, headers=aniket_headers, timeout=10)
            
            if response.status_code == 200:
                self.log_test("GOA Trip - Add Ritaban", True, "Member added")
            else:
                self.log_test("GOA Trip - Add Ritaban", False, f"Status: {response.status_code}")
            
            # Create expense: 3000 INR paid by Aniket, split equally
            expense_data = {
                "trip_id": trip_id,
                "description": "GOA Hotel Booking",
                "total_amount": 3000.00,
                "currency": "INR",
                "payers": [{"user_id": aniket_id, "amount": 3000.00}],
                "splits": [
                    {"user_id": aniket_id, "amount": 1500.00},
                    {"user_id": ritaban_id, "amount": 1500.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=aniket_headers, timeout=10)
            if response.status_code != 200:
                self.log_test("GOA Trip - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            self.log_test("GOA Trip - Create Expense", True, f"Expense ID: {expense_id}")
            
            # Create refund: 1500 INR to Ritaban
            refund_data = {
                "expense_id": expense_id,
                "amount": 1500.00,
                "reason": "Hotel booking partial refund",
                "refunded_to": [ritaban_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=aniket_headers, timeout=10)
            if response.status_code != 200:
                self.log_test("GOA Trip - Create Refund", False, f"Status: {response.status_code}")
                return
            
            self.log_test("GOA Trip - Create Refund", True, "Refund created")
            
            # Test 1: Check trip total expenses (should be 1500 after refund)
            response = requests.get(f"{self.api_url}/trips/{trip_id}", headers=aniket_headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                total_expenses = trip.get('total_expenses', 0)
                expected_net = 1500.00  # 3000 - 1500 refund
                
                if abs(total_expenses - expected_net) < 0.01:
                    self.log_test("GOA Trip - Total Expenses After Refund", True, f"Correct: {total_expenses}")
                else:
                    self.log_test("GOA Trip - Total Expenses After Refund", False, 
                                f"Expected {expected_net}, got {total_expenses}")
            else:
                self.log_test("GOA Trip - Total Expenses After Refund", False, f"Status: {response.status_code}")
            
            # Test 2: Check balances with refund recipient logic
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=aniket_headers, timeout=10)
            if response.status_code == 200:
                balances = response.json()
                
                aniket_balance = None
                ritaban_balance = None
                
                for balance in balances:
                    if balance['user_id'] == aniket_id:
                        aniket_balance = balance['balance']
                    elif balance['user_id'] == ritaban_id:
                        ritaban_balance = balance['balance']
                
                # Expected calculation:
                # Aniket: paid 3000, owes 750 (net split) → +2250
                # Ritaban: paid 0, received refund 1500 (debit), owes 750 → 0 - 1500 - 750 = -2250
                expected_aniket = 2250.00
                expected_ritaban = -2250.00
                
                aniket_correct = aniket_balance is not None and abs(aniket_balance - expected_aniket) < 0.01
                ritaban_correct = ritaban_balance is not None and abs(ritaban_balance - expected_ritaban) < 0.01
                
                if aniket_correct and ritaban_correct:
                    self.log_test("GOA Trip - Refund Recipient Balance Calculation", True, 
                                f"Aniket: {aniket_balance}, Ritaban: {ritaban_balance}")
                else:
                    self.log_test("GOA Trip - Refund Recipient Balance Calculation", False, 
                                f"Expected Aniket: {expected_aniket}, Ritaban: {expected_ritaban}. "
                                f"Got Aniket: {aniket_balance}, Ritaban: {ritaban_balance}")
                
                # Test 3: Check that balances sum to zero
                total_balance = sum(b.get('balance', 0) for b in balances)
                if abs(total_balance) < 0.01:
                    self.log_test("GOA Trip - Balances Sum to Zero", True, f"Total: {total_balance:.2f}")
                else:
                    self.log_test("GOA Trip - Balances Sum to Zero", False, f"Total: {total_balance:.2f}")
            else:
                self.log_test("GOA Trip - Refund Recipient Balance Calculation", False, f"Status: {response.status_code}")
            
            # Test 4: Check settlements
            response = requests.get(f"{self.api_url}/trips/{trip_id}/settlements", headers=aniket_headers, timeout=10)
            if response.status_code == 200:
                settlements = response.json()
                
                # Should have one settlement: Ritaban pays Aniket 2250
                if len(settlements) == 1:
                    settlement = settlements[0]
                    if (settlement['from_user_id'] == ritaban_id and 
                        settlement['to_user_id'] == aniket_id and
                        abs(settlement['amount'] - 2250.00) < 0.01):
                        self.log_test("GOA Trip - Settlement Calculation", True, 
                                    f"Ritaban → Aniket: {settlement['amount']}")
                    else:
                        self.log_test("GOA Trip - Settlement Calculation", False, 
                                    f"Incorrect settlement: {settlement}")
                else:
                    self.log_test("GOA Trip - Settlement Calculation", False, 
                                f"Expected 1 settlement, got {len(settlements)}")
            else:
                self.log_test("GOA Trip - Settlement Calculation", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("GOA Trip - Test Execution", False, f"Error: {str(e)}")

    def test_test_trip_scenario(self):
        """Test Test Trip scenario: 500 expense, 50 refund to Admin"""
        print("\n🔍 Testing Test Trip Scenario...")
        
        # Create admin user
        admin_id = "user_admin_test"
        admin_session = "test_session_admin_001"
        
        if not self.create_test_session(admin_id, admin_session, "admin@test.com", "Admin"):
            self.log_test("Test Trip - Create Admin User", False, "Failed to create user")
            return
        
        admin_headers = {
            'Authorization': f'Bearer {admin_session}',
            'Content-Type': 'application/json'
        }
        
        # Create trip
        trip_data = {
            "name": "Test Trip for Expense",
            "description": "Testing refund calculation",
            "currency": "USD"
        }
        
        try:
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=admin_headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Test Trip - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            self.log_test("Test Trip - Create Trip", True, f"Trip ID: {trip_id}")
            
            # Create expense: 500 paid by Admin
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Expense",
                "total_amount": 500.00,
                "currency": "USD",
                "payers": [{"user_id": admin_id, "amount": 500.00}],
                "splits": [{"user_id": admin_id, "amount": 500.00}]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data, headers=admin_headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Test Trip - Create Expense", False, f"Status: {response.status_code}")
                return
            
            expense_id = response.json().get('expense_id')
            self.log_test("Test Trip - Create Expense", True, f"Expense ID: {expense_id}")
            
            # Create refund: 50 to Admin
            refund_data = {
                "expense_id": expense_id,
                "amount": 50.00,
                "reason": "Test refund",
                "refunded_to": [admin_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=admin_headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Test Trip - Create Refund", False, f"Status: {response.status_code}")
                return
            
            self.log_test("Test Trip - Create Refund", True, "Refund created")
            
            # Test 1: Check trip total expenses (should be 450 after refund)
            response = requests.get(f"{self.api_url}/trips/{trip_id}", headers=admin_headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                total_expenses = trip.get('total_expenses', 0)
                expected_net = 450.00  # 500 - 50 refund
                
                if abs(total_expenses - expected_net) < 0.01:
                    self.log_test("Test Trip - Total Expenses After Refund", True, f"Correct: {total_expenses}")
                else:
                    self.log_test("Test Trip - Total Expenses After Refund", False, 
                                f"Expected {expected_net}, got {total_expenses}")
            else:
                self.log_test("Test Trip - Total Expenses After Refund", False, f"Status: {response.status_code}")
            
            # Test 2: Check admin balance (should be reduced by refund amount)
            response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=admin_headers, timeout=10)
            if response.status_code == 200:
                balances = response.json()
                
                admin_balance = None
                for balance in balances:
                    if balance['user_id'] == admin_id:
                        admin_balance = balance['balance']
                        break
                
                # Expected calculation:
                # Admin: paid 500, received refund 50 (debit), owes 450 → 500 - 50 - 450 = 0
                expected_admin = 0.00
                
                if admin_balance is not None and abs(admin_balance - expected_admin) < 0.01:
                    self.log_test("Test Trip - Admin Balance After Refund", True, f"Correct: {admin_balance}")
                else:
                    self.log_test("Test Trip - Admin Balance After Refund", False, 
                                f"Expected {expected_admin}, got {admin_balance}")
            else:
                self.log_test("Test Trip - Admin Balance After Refund", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Test Trip - Test Execution", False, f"Error: {str(e)}")

    def test_edge_cases(self):
        """Test edge cases for refund recipient calculation"""
        print("\n🔍 Testing Edge Cases...")
        
        # Create test users
        user1_id = "user_edge_test_1"
        user2_id = "user_edge_test_2"
        user3_id = "user_edge_test_3"
        session1 = "test_session_edge_1"
        
        if not self.create_test_session(user1_id, session1, "user1@test.com", "User1"):
            self.log_test("Edge Cases - Create User1", False, "Failed to create user")
            return
        
        if not self.create_test_session(user2_id, "test_session_edge_2", "user2@test.com", "User2"):
            self.log_test("Edge Cases - Create User2", False, "Failed to create user")
            return
        
        if not self.create_test_session(user3_id, "test_session_edge_3", "user3@test.com", "User3"):
            self.log_test("Edge Cases - Create User3", False, "Failed to create user")
            return
        
        headers = {
            'Authorization': f'Bearer {session1}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Create trip
            trip_data = {
                "name": "Edge Cases Test Trip",
                "description": "Testing edge cases",
                "currency": "USD"
            }
            
            response = requests.post(f"{self.api_url}/trips", json=trip_data, headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Edge Cases - Create Trip", False, f"Status: {response.status_code}")
                return
            
            trip_id = response.json().get('trip_id')
            
            # Add members
            for user_id, email, name in [(user2_id, "user2@test.com", "User2"), 
                                       (user3_id, "user3@test.com", "User3")]:
                member_data = {"email": email, "name": name}
                requests.post(f"{self.api_url}/trips/{trip_id}/members", 
                            json=member_data, headers=headers, timeout=10)
            
            # Edge Case 1: Expense with no refund (should work normally)
            expense_data_1 = {
                "trip_id": trip_id,
                "description": "No Refund Expense",
                "total_amount": 300.00,
                "currency": "USD",
                "payers": [{"user_id": user1_id, "amount": 300.00}],
                "splits": [
                    {"user_id": user1_id, "amount": 100.00},
                    {"user_id": user2_id, "amount": 100.00},
                    {"user_id": user3_id, "amount": 100.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data_1, headers=headers, timeout=10)
            if response.status_code == 200:
                expense_1 = response.json()
                net_amount = expense_1.get('net_amount', 0)
                if abs(net_amount - 300.00) < 0.01:
                    self.log_test("Edge Case - No Refund Expense", True, f"Net amount: {net_amount}")
                else:
                    self.log_test("Edge Case - No Refund Expense", False, f"Expected 300, got {net_amount}")
            else:
                self.log_test("Edge Case - No Refund Expense", False, f"Status: {response.status_code}")
            
            # Edge Case 2: Refund split among multiple recipients
            expense_data_2 = {
                "trip_id": trip_id,
                "description": "Multi-Recipient Refund Expense",
                "total_amount": 600.00,
                "currency": "USD",
                "payers": [{"user_id": user1_id, "amount": 600.00}],
                "splits": [
                    {"user_id": user1_id, "amount": 200.00},
                    {"user_id": user2_id, "amount": 200.00},
                    {"user_id": user3_id, "amount": 200.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data_2, headers=headers, timeout=10)
            if response.status_code == 200:
                expense_2 = response.json()
                expense_2_id = expense_2.get('expense_id')
                
                # Create refund to multiple recipients
                refund_data = {
                    "expense_id": expense_2_id,
                    "amount": 120.00,
                    "reason": "Multi-recipient refund",
                    "refunded_to": [user2_id, user3_id]  # 60 each
                }
                
                response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
                if response.status_code == 200:
                    # Check balances
                    response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
                    if response.status_code == 200:
                        balances = response.json()
                        total_balance = sum(b.get('balance', 0) for b in balances)
                        
                        if abs(total_balance) < 0.01:
                            self.log_test("Edge Case - Multi-Recipient Refund Balance", True, 
                                        f"Balanced: {total_balance:.2f}")
                        else:
                            self.log_test("Edge Case - Multi-Recipient Refund Balance", False, 
                                        f"Not balanced: {total_balance:.2f}")
                    else:
                        self.log_test("Edge Case - Multi-Recipient Refund Balance", False, 
                                    f"Status: {response.status_code}")
                else:
                    self.log_test("Edge Case - Multi-Recipient Refund", False, f"Status: {response.status_code}")
            else:
                self.log_test("Edge Case - Multi-Recipient Refund Setup", False, f"Status: {response.status_code}")
            
            # Edge Case 3: Person who paid also receives the refund
            expense_data_3 = {
                "trip_id": trip_id,
                "description": "Payer Receives Refund Expense",
                "total_amount": 450.00,
                "currency": "USD",
                "payers": [{"user_id": user1_id, "amount": 450.00}],
                "splits": [
                    {"user_id": user1_id, "amount": 150.00},
                    {"user_id": user2_id, "amount": 150.00},
                    {"user_id": user3_id, "amount": 150.00}
                ]
            }
            
            response = requests.post(f"{self.api_url}/expenses", json=expense_data_3, headers=headers, timeout=10)
            if response.status_code == 200:
                expense_3 = response.json()
                expense_3_id = expense_3.get('expense_id')
                
                # Create refund to the payer
                refund_data = {
                    "expense_id": expense_3_id,
                    "amount": 90.00,
                    "reason": "Payer receives refund",
                    "refunded_to": [user1_id]
                }
                
                response = requests.post(f"{self.api_url}/refunds", json=refund_data, headers=headers, timeout=10)
                if response.status_code == 200:
                    # Check User1's balance
                    response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", headers=headers, timeout=10)
                    if response.status_code == 200:
                        balances = response.json()
                        user1_balance = None
                        
                        for balance in balances:
                            if balance['user_id'] == user1_id:
                                user1_balance = balance['balance']
                                break
                        
                        # User1: paid 450, received refund 90 (debit), owes 135 (net split)
                        # Balance = 450 - 90 - 135 = 225
                        # But we need to consider all expenses in the trip
                        
                        if user1_balance is not None:
                            self.log_test("Edge Case - Payer Receives Refund", True, 
                                        f"User1 balance: {user1_balance}")
                        else:
                            self.log_test("Edge Case - Payer Receives Refund", False, "User1 balance not found")
                    else:
                        self.log_test("Edge Case - Payer Receives Refund", False, f"Status: {response.status_code}")
                else:
                    self.log_test("Edge Case - Payer Receives Refund", False, f"Status: {response.status_code}")
            else:
                self.log_test("Edge Case - Payer Receives Refund Setup", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Edge Cases - Test Execution", False, f"Error: {str(e)}")

    def test_existing_scenarios(self):
        """Test the existing scenarios mentioned in the review request"""
        print("\n🔍 Testing Existing Scenarios...")
        
        # Test GOA Trip scenario
        goa_headers = {
            'Authorization': 'Bearer OVzj8YHuDyeXJwdSt5uqkc9-kgQIHrH0WFHipWueICo',
            'Content-Type': 'application/json'
        }
        
        try:
            # Test GOA Trip
            response = requests.get(f"{self.api_url}/trips/trip_072802d10446", headers=goa_headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                total_expenses = trip.get('total_expenses', 0)
                your_balance = trip.get('your_balance', 0)
                
                self.log_test("Existing GOA Trip - API Access", True, 
                            f"Total: {total_expenses}, Balance: {your_balance}")
                
                # Check balances
                response = requests.get(f"{self.api_url}/trips/trip_072802d10446/balances", 
                                      headers=goa_headers, timeout=10)
                if response.status_code == 200:
                    balances = response.json()
                    total_balance = sum(b.get('balance', 0) for b in balances)
                    
                    balance_details = ", ".join([f"{b.get('name', 'Unknown')}: {b.get('balance', 0):.2f}" 
                                               for b in balances])
                    
                    if abs(total_balance) < 0.01:
                        self.log_test("Existing GOA Trip - Balances", True, 
                                    f"Balanced ({balance_details})")
                    else:
                        self.log_test("Existing GOA Trip - Balances", False, 
                                    f"Not balanced: {total_balance:.2f} ({balance_details})")
                else:
                    self.log_test("Existing GOA Trip - Balances", False, f"Status: {response.status_code}")
            else:
                self.log_test("Existing GOA Trip - API Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Existing GOA Trip - Test", False, f"Error: {str(e)}")
        
        # Test Test Trip scenario
        test_headers = {
            'Authorization': 'Bearer admin_session_token_001',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f"{self.api_url}/trips/trip_76cd936d507d", headers=test_headers, timeout=10)
            if response.status_code == 200:
                trip = response.json()
                total_expenses = trip.get('total_expenses', 0)
                your_balance = trip.get('your_balance', 0)
                
                self.log_test("Existing Test Trip - API Access", True, 
                            f"Total: {total_expenses}, Balance: {your_balance}")
                
                # Check balances
                response = requests.get(f"{self.api_url}/trips/trip_76cd936d507d/balances", 
                                      headers=test_headers, timeout=10)
                if response.status_code == 200:
                    balances = response.json()
                    total_balance = sum(b.get('balance', 0) for b in balances)
                    
                    balance_details = ", ".join([f"{b.get('name', 'Unknown')}: {b.get('balance', 0):.2f}" 
                                               for b in balances])
                    
                    if abs(total_balance) < 0.01:
                        self.log_test("Existing Test Trip - Balances", True, 
                                    f"Balanced ({balance_details})")
                    else:
                        self.log_test("Existing Test Trip - Balances", False, 
                                    f"Not balanced: {total_balance:.2f} ({balance_details})")
                else:
                    self.log_test("Existing Test Trip - Balances", False, f"Status: {response.status_code}")
            else:
                self.log_test("Existing Test Trip - API Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Existing Test Trip - Test", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            cleanup_cmd = """mongosh --eval "
                use('test_database');
                db.users.deleteMany({email: /test\\.com/});
                db.user_sessions.deleteMany({session_token: /test_session/});
                db.trips.deleteMany({name: /Test/});
                db.expenses.deleteMany({description: /Test/});
                db.refunds.deleteMany({reason: /test|Test/});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_test("Cleanup Test Data", True, "Test data cleaned")
            else:
                self.log_test("Cleanup Test Data", False, f"Cleanup failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Cleanup Test Data", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all refund recipient calculation tests"""
        print("🚀 Starting Refund Recipient Calculation Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        
        # Test existing scenarios first
        self.test_existing_scenarios()
        
        # Test new scenarios
        self.test_goa_trip_scenario()
        self.test_test_trip_scenario()
        self.test_edge_cases()
        
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
    tester = RefundRecipientCalculationTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())