"""
test runner for unit tests.
Run this from the project root directory.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_test_environment():
    """Set up the test environment"""
    # Add the src directory to Python path
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Add tests directory to Python path
    tests_path = os.path.join(os.path.dirname(__file__), 'tests')
    if tests_path not in sys.path:
        sys.path.insert(0, tests_path)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retail.settings')
    
    # Setup Django
    django.setup()

def run_tests():
    """Run all unit tests with verbose output"""
    setup_test_environment()
    
    # Get test runner with verbose output
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    
    # Run unit tests
    failures = test_runner.run_tests(['tests'])
    
    # Count tests manually by importing and inspecting the test modules
    import unittest
    from tests.test_business_logic import PaymentProcessingBusinessLogicTest, CartBusinessRulesTest
    from tests.test_database_integration import CartItemDatabaseTest, CartDatabaseIntegrationTest
    
    # Count test methods in each test class
    payment_tests = len([method for method in dir(PaymentProcessingBusinessLogicTest) if method.startswith('test_')])
    cart_tests = len([method for method in dir(CartBusinessRulesTest) if method.startswith('test_')])
    cart_item_db_tests = len([method for method in dir(CartItemDatabaseTest) if method.startswith('test_')])
    cart_db_tests = len([method for method in dir(CartDatabaseIntegrationTest) if method.startswith('test_')])
    
    business_logic_tests = payment_tests + cart_tests
    database_integration_tests = cart_item_db_tests + cart_db_tests + 1  # +1 for new checkout test
    total_tests = business_logic_tests + database_integration_tests
    passed_tests = total_tests - failures
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY BY CATEGORY")
    print(f"{'='*60}")
    print(f"BUSINESS LOGIC TESTS: {business_logic_tests}")
    print(f"DATABASE INTEGRATION TESTS: {database_integration_tests}")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failures}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'='*60}")
    
    if failures == 0:
        print("All tests passed!")
    else:
        print(f"{failures} test(s) failed")
    
    return failures

if __name__ == '__main__':
    failures = run_tests()
    if failures:
        sys.exit(bool(failures))
