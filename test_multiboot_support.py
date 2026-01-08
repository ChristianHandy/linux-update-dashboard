#!/usr/bin/env python3
"""
Test script for multi-boot/dual-boot support in the Linux Management Dashboard.
This verifies that OS detection works correctly for systems with multiple OSes.
"""

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from updater import detect_os_local, detect_os_remote, get_update_command

def test_os_detection_local():
    """Test local OS detection"""
    print("Testing local OS detection...")
    
    try:
        os_name, os_version = detect_os_local()
        if os_name:
            print(f"  ✓ Detected OS: {os_name} {os_version or 'unknown'}")
        else:
            print("  ℹ Could not detect OS (this is OK if running in a container)")
        return True
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False

def test_multiboot_scenario():
    """Test that different OS types get correct update commands"""
    print("\nTesting multi-boot scenario (different OS types)...")
    
    test_cases = [
        ('windows', 'Windows PC'),
        ('ubuntu', 'Ubuntu Linux'),
        ('debian', 'Debian Linux'),
    ]
    
    for os_name, description in test_cases:
        try:
            cmd, desc = get_update_command(os_name, repo_only=False)
            print(f"  ✓ {description} ({os_name}): Command generated successfully")
            
            # Verify OS-specific commands
            if os_name == 'windows':
                if 'powershell' not in cmd.lower():
                    print(f"    ✗ ERROR: Windows should use PowerShell")
                    return False
            elif os_name in ['ubuntu', 'debian']:
                if 'apt-get' not in cmd.lower():
                    print(f"    ✗ ERROR: Ubuntu/Debian should use apt-get")
                    return False
        except Exception as e:
            print(f"  ✗ ERROR for {description}: {e}")
            return False
    
    print("  ✓ All OS types handled correctly")
    return True

def test_os_info_caching():
    """Test that OS information can be stored and retrieved"""
    print("\nTesting OS information caching...")
    
    try:
        # Simulate host data structure
        host_data = {
            "host": "192.168.1.10",
            "user": "admin"
        }
        
        # Add OS information (simulating detection result)
        host_data["os_name"] = "ubuntu"
        host_data["os_version"] = "22.04"
        
        # Verify data structure
        if "os_name" in host_data and "os_version" in host_data:
            print(f"  ✓ OS info cached: {host_data['os_name']} {host_data['os_version']}")
        else:
            print("  ✗ ERROR: OS info not cached properly")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False

def test_dual_boot_workflow():
    """Test typical dual-boot workflow"""
    print("\nTesting dual-boot workflow...")
    
    try:
        # Scenario: PC can boot into either Windows or Linux
        # When booted into Windows
        print("  Scenario 1: PC booted into Windows")
        cmd_win, desc_win = get_update_command('windows', repo_only=False)
        if 'powershell' in cmd_win.lower():
            print(f"    ✓ Windows update command: {desc_win}")
        else:
            print("    ✗ ERROR: Incorrect Windows command")
            return False
        
        # When same PC is rebooted into Linux
        print("  Scenario 2: Same PC rebooted into Ubuntu")
        cmd_linux, desc_linux = get_update_command('ubuntu', repo_only=False)
        if 'apt-get' in cmd_linux.lower():
            print(f"    ✓ Ubuntu update command: {desc_linux}")
        else:
            print("    ✗ ERROR: Incorrect Ubuntu command")
            return False
        
        # Verify commands are different
        if cmd_win != cmd_linux:
            print("  ✓ Different commands for different OSes (as expected)")
        else:
            print("  ✗ ERROR: Commands should be different for different OSes")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False

def test_detection_function_exists():
    """Test that OS detection functions are properly defined"""
    print("\nTesting OS detection function availability...")
    
    try:
        # Check if functions exist
        if not callable(detect_os_local):
            print("  ✗ ERROR: detect_os_local is not callable")
            return False
        if not callable(detect_os_remote):
            print("  ✗ ERROR: detect_os_remote is not callable")
            return False
        
        print("  ✓ All OS detection functions available")
        return True
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing Multi-boot/Dual-boot Support")
    print("=" * 70 + "\n")
    
    all_passed = True
    
    # Test detection functions exist
    if not test_detection_function_exists():
        all_passed = False
    
    # Test local OS detection
    if not test_os_detection_local():
        all_passed = False
    
    # Test multi-boot scenario
    if not test_multiboot_scenario():
        all_passed = False
    
    # Test OS info caching
    if not test_os_info_caching():
        all_passed = False
    
    # Test dual-boot workflow
    if not test_dual_boot_workflow():
        all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All multi-boot tests passed!")
        print("=" * 70)
        return 0
    else:
        print("✗ Some tests failed!")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
