#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
import uuid

class SplitEaseAPITester:
    def __init__(self, base_url="https://splitease-15.preview.emergentagent.com"):
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

    def test_basic_api_endpoints(self):
        """Test basic API endpoints without authentication"""
        print("\n🔍 Testing Basic API Endpoints...")
        
        # Test root API endpoint
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("API Root Endpoint", success, details)
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Error: {str(e)}")

        # Test currencies endpoint
        try:
            response = requests.get(f"{self.api_url}/currencies", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Currencies count: {len(data)}"
                # Check if it has expected currency structure
                if data and isinstance(data, list) and 'code' in data[0]:
                    details += ", Structure: Valid"
                else:
                    success = False
                    details += ", Structure: Invalid"
            self.log_test("Currencies Endpoint", success, details)
        except Exception as e:
            self.log_test("Currencies Endpoint", False, f"Error: {str(e)}")

    def create_test_user_session(self):
        """Create test user and session in MongoDB using auth_testing.md approach"""
        print("\n🔍 Creating Test User and Session...")
        
        try:
            # Generate test data
            timestamp = int(datetime.now().timestamp())
            self.test_user_id = f"test-user-{timestamp}"
            self.session_token = f"test_session_{timestamp}"
            test_email = f"test.user.{timestamp}@example.com"
            
            # Use mongosh with simpler approach
            import subprocess
            
            # Create user command
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
                print('Session token: ' + sessionToken);
            " """
            
            result = subprocess.run(user_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and "Created user:" in result.stdout:
                self.log_test("Create Test User & Session", True, f"User ID: {self.test_user_id}")
                print(f"📝 Session Token: {self.session_token}")
                return True
            else:
                self.log_test("Create Test User & Session", False, f"Creation failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Create Test User & Session", False, f"Error: {str(e)}")
        
        return False

    def test_authenticated_endpoints(self):
        """Test authenticated API endpoints"""
        if not self.session_token:
            print("⚠️ Skipping authenticated tests - no session token")
            return
            
        print("\n🔍 Testing Authenticated Endpoints...")
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        # Test auth/me endpoint
        try:
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", User: {data.get('name', 'Unknown')}"
            self.log_test("Auth Me Endpoint", success, details)
        except Exception as e:
            self.log_test("Auth Me Endpoint", False, f"Error: {str(e)}")

        # Test trips endpoint
        try:
            response = requests.get(f"{self.api_url}/trips", headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Trips count: {len(data)}"
            self.log_test("Get Trips Endpoint", success, details)
        except Exception as e:
            self.log_test("Get Trips Endpoint", False, f"Error: {str(e)}")

    def test_trip_crud_operations(self):
        """Test trip CRUD operations"""
        if not self.session_token:
            print("⚠️ Skipping trip CRUD tests - no session token")
            return
            
        print("\n🔍 Testing Trip CRUD Operations...")
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        trip_id = None
        
        # Create trip
        try:
            trip_data = {
                "name": "Test Beach Vacation",
                "description": "Test trip for API testing",
                "currency": "USD",
                "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?crop=entropy&cs=srgb&fm=jpg&q=85&w=400"
            }
            
            response = requests.post(f"{self.api_url}/trips", 
                                   json=trip_data, headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                trip_id = data.get('trip_id')
                details += f", Trip ID: {trip_id}"
            self.log_test("Create Trip", success, details)
        except Exception as e:
            self.log_test("Create Trip", False, f"Error: {str(e)}")

        # Get specific trip
        if trip_id:
            try:
                response = requests.get(f"{self.api_url}/trips/{trip_id}", 
                                      headers=headers, timeout=10)
                success = response.status_code == 200
                details = f"Status: {response.status_code}"
                if success:
                    data = response.json()
                    details += f", Trip: {data.get('name', 'Unknown')}"
                self.log_test("Get Specific Trip", success, details)
            except Exception as e:
                self.log_test("Get Specific Trip", False, f"Error: {str(e)}")

            # Test trip balances
            try:
                response = requests.get(f"{self.api_url}/trips/{trip_id}/balances", 
                                      headers=headers, timeout=10)
                success = response.status_code == 200
                details = f"Status: {response.status_code}"
                if success:
                    data = response.json()
                    details += f", Balances count: {len(data)}"
                self.log_test("Get Trip Balances", success, details)
            except Exception as e:
                self.log_test("Get Trip Balances", False, f"Error: {str(e)}")

            # Test trip settlements
            try:
                response = requests.get(f"{self.api_url}/trips/{trip_id}/settlements", 
                                      headers=headers, timeout=10)
                success = response.status_code == 200
                details = f"Status: {response.status_code}"
                if success:
                    data = response.json()
                    details += f", Settlements count: {len(data)}"
                self.log_test("Get Trip Settlements", success, details)
            except Exception as e:
                self.log_test("Get Trip Settlements", False, f"Error: {str(e)}")

        return trip_id

    def test_expense_operations(self, trip_id):
        """Test expense operations"""
        if not self.session_token or not trip_id:
            print("⚠️ Skipping expense tests - no session token or trip ID")
            return
            
        print("\n🔍 Testing Expense Operations...")
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        expense_id = None
        
        # Create expense
        try:
            expense_data = {
                "trip_id": trip_id,
                "description": "Test Hotel Booking",
                "total_amount": 300.00,
                "currency": "USD",
                "category": "accommodation",
                "payers": [{"user_id": self.test_user_id, "amount": 300.00}],
                "splits": [{"user_id": self.test_user_id, "amount": 300.00}]
            }
            
            response = requests.post(f"{self.api_url}/expenses", 
                                   json=expense_data, headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                expense_id = data.get('expense_id')
                details += f", Expense ID: {expense_id}"
            self.log_test("Create Expense", success, details)
        except Exception as e:
            self.log_test("Create Expense", False, f"Error: {str(e)}")

        # Get trip expenses
        try:
            response = requests.get(f"{self.api_url}/expenses/trip/{trip_id}", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Expenses count: {len(data)}"
            self.log_test("Get Trip Expenses", success, details)
        except Exception as e:
            self.log_test("Get Trip Expenses", False, f"Error: {str(e)}")

        return expense_id

    def test_refund_operations(self, expense_id):
        """Test refund operations"""
        if not self.session_token or not expense_id:
            print("⚠️ Skipping refund tests - no session token or expense ID")
            return
            
        print("\n🔍 Testing Refund Operations...")
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        # Create refund
        try:
            refund_data = {
                "expense_id": expense_id,
                "amount": 50.00,
                "reason": "Partial cancellation fee refund",
                "refunded_to": [self.test_user_id]
            }
            
            response = requests.post(f"{self.api_url}/refunds", 
                                   json=refund_data, headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Refund ID: {data.get('refund_id')}"
            self.log_test("Create Refund", success, details)
        except Exception as e:
            self.log_test("Create Refund", False, f"Error: {str(e)}")

        # Get expense refunds
        try:
            response = requests.get(f"{self.api_url}/refunds/expense/{expense_id}", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Refunds count: {len(data)}"
            self.log_test("Get Expense Refunds", success, details)
        except Exception as e:
            self.log_test("Get Expense Refunds", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            import subprocess
            # Clean up test user and session
            cleanup_cmd = f"""mongosh --eval "
                use('test_database');
                db.users.deleteMany({{email: /test\\.user\\./}});
                db.user_sessions.deleteMany({{session_token: /test_session/}});
                db.trips.deleteMany({{name: /Test/}});
                db.expenses.deleteMany({{description: /Test/}});
                db.refunds.deleteMany({{reason: /test|Test/}});
            " """
            
            result = subprocess.run(cleanup_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_test("Cleanup Test Data", True, "Test data cleaned")
            else:
                self.log_test("Cleanup Test Data", False, f"Cleanup failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Cleanup Test Data", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SplitEase Backend API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        
        # Test basic endpoints
        self.test_basic_api_endpoints()
        
        # Create test user and session
        if self.create_test_user_session():
            # Test authenticated endpoints
            self.test_authenticated_endpoints()
            
            # Test trip operations
            trip_id = self.test_trip_crud_operations()
            
            # Test expense operations
            expense_id = self.test_expense_operations(trip_id)
            
            # Test refund operations
            self.test_refund_operations(expense_id)
            
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
    tester = SplitEaseAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())