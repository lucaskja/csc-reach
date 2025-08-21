#!/usr/bin/env python3
"""
macOS Diagnostic Script for CSC-Reach
Checks Outlook installation, permissions, and system configuration.
"""

import subprocess
import sys
from pathlib import Path
import json


def run_command(cmd, timeout=10):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_outlook_installation():
    """Check if Microsoft Outlook is installed."""
    print("🔍 Checking Microsoft Outlook installation...")
    
    outlook_path = Path("/Applications/Microsoft Outlook.app")
    if outlook_path.exists():
        print("✅ Microsoft Outlook is installed")
        
        # Check version
        success, version, error = run_command(
            "mdls -name kMDItemVersion '/Applications/Microsoft Outlook.app'"
        )
        if success and version:
            print(f"   Version: {version.split('=')[1].strip().strip('\"')}")
        
        return True
    else:
        print("❌ Microsoft Outlook is NOT installed")
        print("   Please install Microsoft Outlook from the Mac App Store or Microsoft website")
        return False


def check_outlook_running():
    """Check if Outlook is currently running."""
    print("\n🔍 Checking if Outlook is running...")
    
    success, output, error = run_command("pgrep -f 'Microsoft Outlook'")
    if success:
        print("✅ Microsoft Outlook is currently running")
        return True
    else:
        print("⚠️  Microsoft Outlook is not running")
        print("   Try starting Outlook manually first")
        return False


def check_applescript_access():
    """Check if AppleScript can access Outlook."""
    print("\n🔍 Testing AppleScript access to Outlook...")
    
    script = '''
    try
        tell application "Microsoft Outlook"
            return "accessible"
        end tell
    on error errMsg
        return "error: " & errMsg
    end try
    '''
    
    success, output, error = run_command(f"osascript -e '{script}'")
    if success and "accessible" in output:
        print("✅ AppleScript can access Outlook")
        return True
    else:
        print("❌ AppleScript cannot access Outlook")
        if error:
            print(f"   Error: {error}")
        if output and "error:" in output:
            print(f"   AppleScript error: {output}")
        print("   You may need to grant automation permissions")
        return False


def check_system_events_access():
    """Check if we can access System Events (optional)."""
    print("\n🔍 Testing System Events access (optional)...")
    
    script = '''
    try
        tell application "System Events"
            return "accessible"
        end tell
    on error errMsg
        return "error: " & errMsg
    end try
    '''
    
    success, output, error = run_command(f"osascript -e '{script}'")
    if success and "accessible" in output:
        print("✅ System Events is accessible")
        return True
    else:
        print("⚠️  System Events is not accessible (this is OK)")
        print("   CSC-Reach will use alternative methods")
        return False


def check_python_dependencies():
    """Check if required Python dependencies are available."""
    print("\n🔍 Checking Python dependencies...")
    
    dependencies = [
        ("ScriptingBridge", "pyobjc-framework-ScriptingBridge"),
        ("Foundation", "pyobjc-framework-Cocoa"),
    ]
    
    all_good = True
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {module} is available")
        except ImportError:
            print(f"❌ {module} is missing")
            print(f"   Install with: pip install {package}")
            all_good = False
    
    return all_good


def test_email_creation():
    """Test creating a draft email in Outlook."""
    print("\n🔍 Testing email draft creation...")
    
    script = '''
    try
        tell application "Microsoft Outlook"
            set newMessage to make new outgoing message
            set subject of newMessage to "CSC-Reach Test Email"
            set content of newMessage to "This is a test email created by CSC-Reach diagnostic script."
            make new recipient at newMessage with properties {email address:{address:"test@example.com"}}
            open newMessage
            return "success"
        end tell
    on error errMsg
        return "error: " & errMsg
    end try
    '''
    
    success, output, error = run_command(f"osascript -e '{script}'")
    if success and "success" in output:
        print("✅ Successfully created test email draft")
        print("   Check Outlook for a draft email with subject 'CSC-Reach Test Email'")
        print("   You can delete this test email")
        return True
    else:
        print("❌ Failed to create test email")
        if error:
            print(f"   Error: {error}")
        if output and "error:" in output:
            print(f"   AppleScript error: {output}")
        return False


def check_permissions_database():
    """Check macOS permissions database."""
    print("\n🔍 Checking macOS permissions database...")
    
    # Check for automation permissions
    success, output, error = run_command(
        "sqlite3 ~/Library/Application\\ Support/com.apple.TCC/TCC.db "
        "\"SELECT service, client, auth_value FROM access WHERE service='kTCCServiceAppleEvents';\""
    )
    
    if success and output:
        print("📋 Automation permissions found:")
        for line in output.split('\n'):
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 3:
                    service, client, auth = parts[0], parts[1], parts[2]
                    status = "✅ Allowed" if auth == "1" else "❌ Denied"
                    print(f"   {client}: {status}")
    else:
        print("⚠️  Could not read permissions database")


def main():
    """Run all diagnostic checks."""
    print("🚀 CSC-Reach macOS Diagnostic Tool")
    print("=" * 50)
    
    checks = [
        ("Outlook Installation", check_outlook_installation),
        ("Outlook Running", check_outlook_running),
        ("AppleScript Access", check_applescript_access),
        ("System Events Access", check_system_events_access),
        ("Python Dependencies", check_python_dependencies),
        ("Email Creation Test", test_email_creation),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results[name] = False
    
    # Check permissions database (may fail on newer macOS versions)
    try:
        check_permissions_database()
    except Exception as e:
        print(f"⚠️  Permissions database check failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! CSC-Reach should work correctly.")
    else:
        print("\n⚠️  Some checks failed. Please review the issues above.")
        print("\nCommon solutions:")
        print("1. Install Microsoft Outlook if missing")
        print("2. Grant automation permissions in System Preferences")
        print("3. Start Outlook manually first")
        print("4. Install missing Python dependencies")
        print("\nSee docs/user/macos_permissions_guide.md for detailed instructions")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)