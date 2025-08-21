#!/usr/bin/env python3
"""
Test script for Outlook integration on macOS.
Creates a test draft email to verify permissions and setup.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from multichannel_messaging.services.outlook_macos import OutlookMacOSService
    from multichannel_messaging.core.models import Customer, MessageTemplate
    from multichannel_messaging.utils.logger import get_logger
except ImportError as e:
    print(f"❌ Failed to import CSC-Reach modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def test_outlook_integration():
    """Test Outlook integration with a draft email."""
    print("🚀 Testing CSC-Reach Outlook Integration")
    print("=" * 50)
    
    try:
        # Initialize Outlook service
        print("🔍 Initializing Outlook service...")
        outlook_service = OutlookMacOSService()
        print("✅ Outlook service initialized")
        
        # Check permissions
        print("\n🔍 Checking permissions...")
        has_permissions, issues = outlook_service.check_permissions()
        
        if not has_permissions:
            print("❌ Permission issues found:")
            for issue in issues:
                print(f"   - {issue}")
            print("\n💡 Solutions:")
            print("   1. Install Microsoft Outlook if missing")
            print("   2. Grant automation permissions in System Preferences")
            print("   3. See docs/user/macos_permissions_guide.md for detailed help")
            return False
        
        print("✅ All permissions are OK")
        
        # Check if Outlook is running
        print("\n🔍 Checking if Outlook is running...")
        if outlook_service.is_outlook_running():
            print("✅ Outlook is running")
        else:
            print("⚠️  Outlook is not running, attempting to start...")
            if outlook_service.start_outlook():
                print("✅ Outlook started successfully")
            else:
                print("❌ Failed to start Outlook")
                return False
        
        # Create test customer and template
        print("\n🔍 Creating test email...")
        test_customer = Customer(
            name="Test User",
            email="test@example.com",
            company="Test Company",
            phone="555-0123"
        )
        
        test_template = MessageTemplate(
            name="Test Template",
            subject="CSC-Reach Integration Test - {name}",
            content="""Hello {name},

This is a test email created by CSC-Reach to verify the Outlook integration is working correctly.

Company: {company}
Email: {email}
Phone: {phone}

You can safely delete this draft email.

Best regards,
CSC-Reach Test System""",
            channel="email"
        )
        
        # Create draft email
        print("📧 Creating draft email in Outlook...")
        success = outlook_service.create_draft_email(test_customer, test_template)
        
        if success:
            print("✅ Test draft email created successfully!")
            print("\n🎉 Integration test PASSED!")
            print("\n📋 Next steps:")
            print("   1. Check Outlook for a draft email with subject 'CSC-Reach Integration Test - Test User'")
            print("   2. Review the draft content to ensure formatting is correct")
            print("   3. Delete the test draft when you're done")
            print("   4. CSC-Reach is ready to use!")
            return True
        else:
            print("❌ Failed to create test draft email")
            print("\n🔧 Troubleshooting:")
            print("   1. Check the logs for detailed error messages")
            print("   2. Ensure Outlook is running and responsive")
            print("   3. Try running the diagnostic script: python scripts/dev/macos_diagnostic.py")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check that Microsoft Outlook is installed")
        print("   2. Grant automation permissions in System Preferences")
        print("   3. Run the diagnostic script: python scripts/dev/macos_diagnostic.py")
        print("   4. See docs/user/macos_permissions_guide.md for detailed help")
        return False


def main():
    """Run the integration test."""
    success = test_outlook_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 INTEGRATION TEST PASSED")
        print("CSC-Reach is ready to send emails through Outlook!")
    else:
        print("❌ INTEGRATION TEST FAILED")
        print("Please resolve the issues above before using CSC-Reach")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)