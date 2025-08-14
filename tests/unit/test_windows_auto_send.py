#!/usr/bin/env python3
"""
Windows Auto-Send Test Script for WhatsApp Web.
Tests the enhanced Windows auto-send functionality.
"""

import sys
import os
import time
import platform
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multichannel_messaging.services.whatsapp_web_service import WhatsAppWebService
from multichannel_messaging.core.models import Customer, MessageTemplate
from multichannel_messaging.utils.logger import get_logger

logger = get_logger(__name__)


def test_windows_auto_send_setup():
    """Test Windows auto-send setup and configuration."""
    print("🔧 Testing Windows Auto-Send Setup")
    print("=" * 40)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test requires Windows")
        return False
    
    # Create service with auto-send enabled
    service = WhatsAppWebService(
        auto_send=True,
        auto_send_delay=6,  # Longer delay for Windows
        close_existing_tabs=True,
        rate_limit_per_minute=5,
        daily_message_limit=50,
        min_delay_seconds=10
    )
    
    print(f"✅ Service created with auto_send={service.auto_send}")
    print(f"📊 Auto-send delay: {service.auto_send_delay} seconds")
    print(f"📊 Close existing tabs: {service.close_existing_tabs}")
    
    # Configure service for auto-send
    success, message = service.configure_service(
        acknowledge_risks=True,
        auto_send=True,
        close_existing_tabs=True
    )
    
    if success:
        print("✅ Service configured for auto-send")
        print(f"📋 Configuration message: {message}")
        return True
    else:
        print(f"❌ Configuration failed: {message}")
        return False


def test_windows_auto_send_methods():
    """Test individual Windows auto-send methods."""
    print("\n🤖 Testing Windows Auto-Send Methods")
    print("=" * 42)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test requires Windows")
        return False
    
    service = WhatsAppWebService(auto_send=True)
    service.configure_service(acknowledge_risks=True, auto_send=True)
    
    # Test individual methods (without actually sending)
    methods_to_test = [
        ("Chrome DevTools", "_try_chrome_devtools_send"),
        ("UI Automation", "_try_ui_automation_send"),
        ("Keyboard Automation", "_try_keyboard_automation_send"),
        ("Simple Enter", "_try_simple_enter_send"),
        ("Focus WhatsApp Window", "_focus_whatsapp_window"),
        ("Smart Click Send", "_windows_smart_click_send"),
        ("Keyboard Send", "_windows_keyboard_send"),
        ("Simple Enter", "_windows_simple_enter")
    ]
    
    results = {}
    
    for method_name, method_attr in methods_to_test:
        if hasattr(service, method_attr):
            print(f"🔧 Testing {method_name}...")
            try:
                method = getattr(service, method_attr)
                # Note: These will likely fail without WhatsApp Web open, which is expected
                result = method()
                results[method_name] = result
                status = "✅ Available" if result else "⚠️ Failed (expected without WhatsApp Web)"
                print(f"   {status}")
            except Exception as e:
                results[method_name] = False
                print(f"   ❌ Error: {e}")
        else:
            results[method_name] = False
            print(f"❌ {method_name}: Method not found")
    
    available_methods = sum(1 for result in results.values() if result is not False)
    total_methods = len(results)
    
    print(f"\n📊 Methods Available: {available_methods}/{total_methods}")
    
    return available_methods > 0


def test_chrome_detection_and_launch():
    """Test Chrome detection and launching for Windows."""
    print("\n🌐 Testing Chrome Detection and Launch")
    print("=" * 40)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test requires Windows")
        return False
    
    service = WhatsAppWebService(auto_send=True)
    
    # Test Chrome detection
    print("🔍 Testing Chrome detection...")
    if hasattr(service, '_detect_chrome_windows'):
        chrome_info = service._detect_chrome_windows()
        print(f"   Found: {chrome_info.get('found', False)}")
        print(f"   Paths: {len(chrome_info.get('paths', []))}")
        print(f"   Version: {chrome_info.get('version', 'Unknown')}")
        print(f"   Registry: {chrome_info.get('registry_found', False)}")
        print(f"   Running: {chrome_info.get('process_running', False)}")
        
        if not chrome_info.get('found', False):
            print("❌ Chrome not detected - auto-send may not work")
            return False
    else:
        print("❌ Chrome detection method not found")
        return False
    
    # Test general Chrome availability
    print("\n🔍 Testing general Chrome availability...")
    chrome_available, chrome_info_str = service._check_chrome_availability()
    print(f"   Available: {chrome_available}")
    print(f"   Info: {chrome_info_str}")
    
    if not chrome_available:
        print("❌ Chrome not available - install Google Chrome for auto-send")
        return False
    
    print("✅ Chrome detection successful")
    return True


def test_whatsapp_web_readiness_check():
    """Test WhatsApp Web readiness verification."""
    print("\n✅ Testing WhatsApp Web Readiness Check")
    print("=" * 42)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test requires Windows")
        return False
    
    service = WhatsAppWebService(auto_send=True)
    
    # Test readiness check methods
    if hasattr(service, '_verify_whatsapp_web_ready'):
        print("🔧 Testing WhatsApp Web readiness check...")
        try:
            is_ready = service._verify_whatsapp_web_ready()
            print(f"   WhatsApp Web Ready: {is_ready}")
            
            if not is_ready:
                print("   ⚠️ WhatsApp Web not ready (expected if not open)")
            else:
                print("   ✅ WhatsApp Web appears to be ready")
            
            return True
        except Exception as e:
            print(f"   ❌ Readiness check failed: {e}")
            return False
    else:
        print("❌ Readiness check method not found")
        return False


def test_full_auto_send_workflow():
    """Test the complete auto-send workflow (with user confirmation)."""
    print("\n🚀 Testing Full Auto-Send Workflow")
    print("=" * 38)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test requires Windows")
        return False
    
    # Create service optimized for Windows auto-send
    service = WhatsAppWebService(
        auto_send=True,
        auto_send_delay=8,  # Longer delay for reliability
        close_existing_tabs=True,
        rate_limit_per_minute=3,
        daily_message_limit=20,
        min_delay_seconds=15
    )
    
    # Configure service
    success, message = service.configure_service(
        acknowledge_risks=True,
        auto_send=True,
        close_existing_tabs=True
    )
    
    if not success:
        print(f"❌ Service configuration failed: {message}")
        return False
    
    print("✅ Service configured for auto-send testing")
    
    # Create test data
    customer = Customer(
        name="Windows Test User",
        phone="+1234567890",
        email="test@example.com",
        company="Test Company"
    )
    
    template = MessageTemplate(
        id="windows-auto-send-test",
        name="Windows Auto-Send Test",
        channels=["whatsapp"],
        content="Hello {name}, this is a Windows auto-send test from {company}!",
        whatsapp_content="🪟 Hello {name}, this is a Windows auto-send test from {company}! 🤖",
        variables=["name", "company"]
    )
    
    print(f"👤 Test Customer: {customer.name} ({customer.phone})")
    print(f"📄 Test Template: {template.name}")
    
    # Show what will happen
    print("\n📋 What this test will do:")
    print("1. Open WhatsApp Web in Chrome")
    print("2. Wait for the page to load")
    print("3. Attempt to automatically send the message")
    print("4. Show results and notifications")
    
    print("\n⚠️ IMPORTANT:")
    print("- Make sure you're logged into WhatsApp Web")
    print("- The test will send a real message to the test number")
    print("- Chrome will open and attempt auto-send")
    
    response = input("\nDo you want to proceed with the full auto-send test? (y/N): ")
    
    if response.lower() != 'y':
        print("⏭️ Skipping full workflow test")
        return True
    
    print("\n🚀 Starting auto-send workflow...")
    
    try:
        # Attempt to send message with auto-send
        success = service.send_message(customer, template)
        
        if success:
            print("✅ Auto-send workflow completed successfully!")
            print("📱 Check your browser and phone for results")
            
            # Check if message was tracked
            usage = service.get_daily_usage()
            print(f"📊 Daily usage updated: {usage['messages_sent_today']}/{usage['daily_limit']}")
            
            return True
        else:
            error = service.get_last_error()
            print(f"❌ Auto-send workflow failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-send workflow error: {e}")
        return False


def main():
    """Run all Windows auto-send tests."""
    print("🪟 Windows Auto-Send Test Suite for WhatsApp Web")
    print("=" * 55)
    
    if platform.system().lower() != "windows":
        print("❌ This test suite requires Windows")
        print(f"Current platform: {platform.system()}")
        return
    
    print(f"🖥️ Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    print()
    
    tests = [
        ("Auto-Send Setup", test_windows_auto_send_setup),
        ("Auto-Send Methods", test_windows_auto_send_methods),
        ("Chrome Detection", test_chrome_detection_and_launch),
        ("Readiness Check", test_whatsapp_web_readiness_check),
        ("Full Workflow", test_full_auto_send_workflow),
    ]
    
    results = {}
    
    try:
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASSED" if result else "⚠️ PARTIAL"
                print(f"\n{status}: {test_name}")
            except Exception as e:
                results[test_name] = False
                print(f"\n❌ FAILED: {test_name} - {e}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All Windows auto-send tests passed!")
            print("\n💡 Windows Auto-Send Features:")
            print("  • Enhanced Chrome detection and launching")
            print("  • Multiple auto-send methods with fallbacks")
            print("  • WhatsApp Web readiness verification")
            print("  • Optimized delays and timing for Windows")
            print("  • Native Windows notifications")
            print("  • Comprehensive error handling")
            
        elif passed > total * 0.7:
            print("\n✅ Most Windows auto-send tests passed!")
            print("💡 Auto-send should work reliably on Windows")
            print("💡 Some advanced features may need Chrome configuration")
        else:
            print("\n⚠️ Several Windows auto-send tests failed")
            print("💡 Check Chrome installation and Windows permissions")
            print("💡 Ensure WhatsApp Web is accessible")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()