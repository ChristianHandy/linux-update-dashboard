#!/usr/bin/env python3
"""
Test script to verify URL redirect security fixes
Tests that URL redirects are properly validated to prevent open redirect attacks
"""
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_safe_redirect_url_validation():
    """Test the is_safe_redirect_url function with various inputs"""
    print("Testing URL redirect validation function...")
    try:
        from app import is_safe_redirect_url
        
        test_cases = [
            # Safe URLs (relative paths)
            ("/index", True, "Relative path with leading slash"),
            ("/dashboard", True, "Another relative path"),
            ("/users/profile", True, "Nested relative path"),
            ("/update/host1", True, "Relative path with parameter"),
            
            # Unsafe URLs (external redirects)
            ("http://evil.com", False, "Absolute HTTP URL"),
            ("https://evil.com", False, "Absolute HTTPS URL"),
            ("//evil.com", False, "Protocol-relative URL"),
            ("javascript:alert(1)", False, "JavaScript protocol"),
            ("data:text/html,<script>alert(1)</script>", False, "Data URL"),
            
            # Edge cases
            ("", False, "Empty string"),
            (None, False, "None value"),
            ("relative", False, "Relative path without leading slash"),
            ("http://localhost:5000/index", False, "Localhost absolute URL"),
        ]
        
        all_passed = True
        for url, expected, description in test_cases:
            result = is_safe_redirect_url(url)
            status = "✓" if result == expected else "✗"
            if result != expected:
                all_passed = False
            print(f"  {status} {description}: '{url}' -> {result} (expected {expected})")
        
        if all_passed:
            print("✓ All URL validation tests passed")
            return True
        else:
            print("✗ Some URL validation tests failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_safe_redirect_url():
    """Test the get_safe_redirect_url function"""
    print("\nTesting safe redirect URL getter...")
    try:
        from app import get_safe_redirect_url
        
        test_cases = [
            # Should return the URL if safe
            ("/index", "/default", "/index", "Safe URL returned as-is"),
            ("/dashboard", "/home", "/dashboard", "Another safe URL"),
            
            # Should return default if unsafe
            ("http://evil.com", "/default", "/default", "Unsafe URL returns default"),
            ("//evil.com", "/home", "/home", "Protocol-relative URL returns default"),
            ("", "/index", "/index", "Empty string returns default"),
            (None, "/dashboard", "/dashboard", "None returns default"),
        ]
        
        all_passed = True
        for url, default, expected, description in test_cases:
            result = get_safe_redirect_url(url, default)
            status = "✓" if result == expected else "✗"
            if result != expected:
                all_passed = False
            print(f"  {status} {description}: get_safe_redirect_url('{url}', '{default}') -> '{result}' (expected '{expected}')")
        
        if all_passed:
            print("✓ All safe redirect getter tests passed")
            return True
        else:
            print("✗ Some safe redirect getter tests failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_login_redirect_security():
    """Test that login route validates redirect URLs"""
    print("\nTesting login route redirect security...")
    try:
        from app import app
        import user_management
        
        # Initialize the database
        user_management.init_user_db()
        
        with app.test_client() as client:
            # Create a test user
            user_id = user_management.create_user('testrediruser', 'testpass123', None, ['admin'])
            if not user_id:
                # User might already exist, try to get it
                user_id = user_management.verify_password('testrediruser', 'testpass123')
            
            # Test 1: Safe redirect URL (relative path)
            print("  Testing safe redirect URL...")
            response = client.post('/', data={
                'user': 'testrediruser',
                'pass': 'testpass123'
            }, query_string={'next': '/dashboard'}, follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if location == '/dashboard':
                    print("  ✓ Safe redirect URL works correctly")
                else:
                    print(f"  ✗ Expected redirect to '/dashboard', got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            # Test 2: Unsafe redirect URL (external site) - should use default
            print("  Testing unsafe redirect URL...")
            response = client.post('/', data={
                'user': 'testrediruser',
                'pass': 'testpass123'
            }, query_string={'next': 'http://evil.com'}, follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                # Should redirect to the default (index) instead of the unsafe URL
                if location.endswith('/index') or location == '/index':
                    print("  ✓ Unsafe redirect URL correctly defaults to safe URL")
                else:
                    print(f"  ✗ Expected redirect to index, got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            # Test 3: Protocol-relative URL attack
            print("  Testing protocol-relative URL...")
            response = client.post('/', data={
                'user': 'testrediruser',
                'pass': 'testpass123'
            }, query_string={'next': '//evil.com'}, follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                # Should redirect to the default instead of the protocol-relative URL
                if location.endswith('/index') or location == '/index':
                    print("  ✓ Protocol-relative URL correctly blocked")
                else:
                    print(f"  ✗ Expected redirect to index, got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            print("✓ All login redirect security tests passed")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_referrer_redirect_security():
    """Test that referrer-based redirects are validated"""
    print("\nTesting referrer-based redirect security...")
    try:
        from app import app
        import user_management
        
        # Initialize the database
        user_management.init_user_db()
        
        with app.test_client() as client:
            # Create and login as test user
            user_id = user_management.create_user('testreferuser', 'testpass123', None, ['admin'])
            if not user_id:
                user_id = user_management.verify_password('testreferuser', 'testpass123')
            
            # Login
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['username'] = 'testreferuser'
                sess['login'] = True
            
            # Test 1: Safe referrer (relative URL)
            print("  Testing safe referrer URL...")
            response = client.get('/dashboard_version/dismiss',
                                headers={'Referer': '/dashboard'},
                                follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if location == '/dashboard':
                    print("  ✓ Safe referrer URL works correctly")
                else:
                    print(f"  ✗ Expected redirect to '/dashboard', got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            # Test 2: Unsafe referrer (external site)
            print("  Testing unsafe referrer URL...")
            response = client.get('/dashboard_version/dismiss',
                                headers={'Referer': 'http://evil.com'},
                                follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                # Should redirect to index instead of the unsafe referrer
                if location.endswith('/index') or location == '/index':
                    print("  ✓ Unsafe referrer correctly defaults to safe URL")
                else:
                    print(f"  ✗ Expected redirect to index, got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            # Test 3: No referrer (should use default)
            print("  Testing missing referrer...")
            response = client.get('/dashboard_version/dismiss',
                                follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if location.endswith('/index') or location == '/index':
                    print("  ✓ Missing referrer correctly uses default")
                else:
                    print(f"  ✗ Expected redirect to index, got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            print("✓ All referrer redirect security tests passed")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_url_for_redirects():
    """Test that url_for is used for constructing redirect URLs"""
    print("\nTesting url_for redirect construction...")
    try:
        from app import app
        import user_management
        
        # Initialize the database
        user_management.init_user_db()
        
        with app.test_client() as client:
            # Create and login as test user with operator role
            user_id = user_management.create_user('testurlforuser', 'testpass123', None, ['operator'])
            if not user_id:
                user_id = user_management.verify_password('testurlforuser', 'testpass123')
            else:
                # Ensure user has operator role
                user_management.set_user_roles(user_id, ['operator'])
            
            # Login
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['username'] = 'testurlforuser'
                sess['login'] = True
            
            # Test that update route uses url_for
            # We can't easily test the internal implementation, but we can verify
            # the redirect works and uses a proper path
            print("  Testing update route redirect...")
            
            # Add a test host
            import json
            hosts_file = os.path.join(os.path.dirname(__file__), 'hosts.json')
            hosts = {'testhost': {'host': 'localhost', 'user': 'testuser'}}
            with open(hosts_file, 'w') as f:
                json.dump(hosts, f)
            
            # The update route will start a thread and redirect
            response = client.get('/update/testhost', follow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                # Should redirect to /progress/testhost (constructed with url_for)
                if '/progress/testhost' in location:
                    print("  ✓ Update route correctly redirects using url_for")
                else:
                    print(f"  ✗ Expected redirect to progress page, got '{location}'")
                    return False
            else:
                print(f"  ✗ Expected 302 redirect, got {response.status_code}")
                return False
            
            print("✓ All url_for redirect tests passed")
            return True
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("URL Redirect Security Fix Verification Test Suite")
    print("=" * 70)
    
    tests = [
        test_safe_redirect_url_validation,
        test_get_safe_redirect_url,
        test_login_redirect_security,
        test_referrer_redirect_security,
        test_url_for_redirects,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 70)
    
    if all(results):
        print("\n✓ All tests passed! URL redirect security fixes are working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
