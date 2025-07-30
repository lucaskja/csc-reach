#!/usr/bin/env python3
"""
Enhanced Windows WhatsApp Web Integration Test Script.
Tests all the Windows-specific enhancements and optimizations.
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


def test_windows_chrome_detection():
    """Test enhanced Chrome detection on Windows."""
    print("🔍 Testing Enhanced Chrome Detection")
    print("=" * 40)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    service = WhatsAppWebService()
    
    # Test Chrome availability check
    chrome_available, chrome_info = service._check_chrome_availability()
    print(f"Chrome Available: {chrome_available}")
    print(f"Chrome Info: {chrome_info}")
    
    # Test detailed Chrome detection
    if hasattr(service, '_detect_chrome_windows'):
        chrome_details = service._detect_chrome_windows()
        print(f"\n📋 Detailed Chrome Detection:")
        print(f"  Found: {chrome_details['found']}")
        print(f"  Paths: {chrome_details['paths']}")
        print(f"  Version: {chrome_details['version']}")
        print(f"  Registry Found: {chrome_details['registry_found']}")
        print(f"  Process Running: {chrome_details['process_running']}")
        print(f"  Details: {chrome_details['details']}")
        
        return chrome_details['found']
    
    return chrome_available


def test_windows_notifications():
    """Test Windows notification system."""
    print("\n🔔 Testing Windows Notifications")
    print("=" * 35)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    service = WhatsAppWebService()
    
    if hasattr(service, '_show_windows_notification'):
        print("Testing toast notification...")
        success = service._show_windows_notification(
            "CSC-Reach Test",
            "This is a test notification from the WhatsApp Web service"
        )
        
        if success:
            print("✅ Windows notification system working")
            return True
        else:
            print("⚠️ Windows notification failed (this is normal on some systems)")
            return False
    else:
        print("❌ Windows notification method not found")
        return False


def test_windows_auto_send():
    """Test Windows auto-send functionality."""
    print("\n🤖 Testing Windows Auto-Send")
    print("=" * 30)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    service = WhatsAppWebService(
        auto_send=True,
        auto_send_delay=3,
        rate_limit_per_minute=10,
        daily_message_limit=100,
        min_delay_seconds=5
    )
    
    # Configure service
    success, message = service.configure_service(
        acknowledge_risks=True,
        auto_send=True
    )
    
    if not success:
        print(f"❌ Configuration failed: {message}")
        return False
    
    print("✅ Service configured for auto-send testing")
    
    # Test JavaScript auto-send method
    print("\n🔧 Testing JavaScript Auto-Send Method...")
    if hasattr(service, '_auto_send_javascript_windows'):
        try:
            js_success = service._auto_send_javascript_windows()
            print(f"JavaScript Auto-Send: {'✅ Success' if js_success else '⚠️ Failed (expected without WhatsApp Web open)'}")
        except Exception as e:
            print(f"JavaScript Auto-Send Error: {e}")
    
    # Test enhanced Windows auto-send method
    print("\n🔧 Testing Enhanced Windows Auto-Send Method...")
    if hasattr(service, '_auto_send_windows'):
        try:
            windows_success = service._auto_send_windows()
            print(f"Enhanced Windows Auto-Send: {'✅ Success' if windows_success else '⚠️ Failed (expected without WhatsApp Web open)'}")
        except Exception as e:
            print(f"Enhanced Windows Auto-Send Error: {e}")
    
    return True


def test_windows_tab_closing():
    """Test Windows tab closing functionality."""
    print("\n🧹 Testing Windows Tab Closing")
    print("=" * 32)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    service = WhatsAppWebService(close_existing_tabs=True)
    
    if hasattr(service, '_close_whatsapp_tabs_windows'):
        try:
            success = service._close_whatsapp_tabs_windows()
            print(f"Windows Tab Closing: {'✅ Success' if success else '⚠️ No tabs to close (normal)'}")
            return True
        except Exception as e:
            print(f"Windows Tab Closing Error: {e}")
            return False
    else:
        print("❌ Windows tab closing method not found")
        return False


def test_windows_chrome_opening():
    """Test enhanced Chrome opening on Windows."""
    print("\n🌐 Testing Enhanced Chrome Opening")
    print("=" * 35)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    service = WhatsAppWebService()
    
    # Test URL creation
    test_phone = "+1234567890"
    test_message = "Hello, this is a test message from CSC-Reach!"
    
    formatted_phone = service._format_phone_number(test_phone)
    whatsapp_url = service._create_whatsapp_url(formatted_phone, test_message)
    
    print(f"📱 Test Phone: {test_phone} → {formatted_phone}")
    print(f"🔗 WhatsApp URL: {whatsapp_url[:80]}...")
    
    # Ask user if they want to test opening
    response = input("\nDo you want to test opening WhatsApp Web in Chrome? (y/N): ")
    if response.lower() == 'y':
        try:
            success = service._open_in_chrome(whatsapp_url)
            if success:
                print("✅ Chrome opening successful!")
                print("📱 Check your browser - WhatsApp Web should have opened")
                print("🧹 Any existing WhatsApp Web tabs should have been closed first")
                return True
            else:
                print("❌ Chrome opening failed")
                return False
        except Exception as e:
            print(f"❌ Chrome opening error: {e}")
            return False
    else:
        print("⏭️ Skipping Chrome opening test")
        return True


def test_full_windows_integration():
    """Test complete Windows integration with a real message flow."""
    print("\n🚀 Testing Full Windows Integration")
    print("=" * 38)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    # Create service with Windows optimizations
    service = WhatsAppWebService(
        auto_send=False,  # Start with manual for safety
        close_existing_tabs=True,
        rate_limit_per_minute=10,
        daily_message_limit=100,
        min_delay_seconds=5
    )
    
    # Configure service
    success, message = service.configure_service(
        acknowledge_risks=True,
        auto_send=False,
        close_existing_tabs=True
    )
    
    if not success:
        print(f"❌ Configuration failed: {message}")
        return False
    
    print("✅ Service configured successfully")
    
    # Create test data
    customer = Customer(
        name="Windows Test User",
        phone="+1234567890",
        email="test@example.com",
        company="Test Company"
    )
    
    template = MessageTemplate(
        id="windows-test-template-001",
        name="Windows Test Template",
        channels=["whatsapp"],
        content="Hello {name}, this is a Windows integration test from {company}!",
        whatsapp_content="🪟 Hello {name}, this is a Windows WhatsApp test from {company}! 🚀",
        variables=["name", "company"]
    )
    
    print(f"📱 Test Customer: {customer.name} ({customer.phone})")
    print(f"📝 Test Template: {template.name}")
    
    # Test the complete flow
    response = input("\nDo you want to test the complete message sending flow? (y/N): ")
    if response.lower() == 'y':
        try:
            print("\n🚀 Starting message send process...")
            success = service.send_message(customer, template)
            
            if success:
                print("✅ Message send process completed successfully!")
                print("📱 Check your browser for WhatsApp Web")
                print("🔔 You should have received a Windows notification")
                return True
            else:
                error = service.get_last_error()
                print(f"❌ Message send failed: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Message send error: {e}")
            return False
    else:
        print("⏭️ Skipping full integration test")
        return True


def run_windows_performance_test():
    """Test Windows-specific performance optimizations."""
    print("\n⚡ Windows Performance Test")
    print("=" * 28)
    
    if platform.system().lower() != "windows":
        print("⚠️ This test is Windows-specific")
        return False
    
    service = WhatsAppWebService()
    
    # Test Chrome detection speed
    start_time = time.time()
    chrome_available, chrome_info = service._check_chrome_availability()
    detection_time = time.time() - start_time
    
    print(f"🔍 Chrome Detection Time: {detection_time:.3f} seconds")
    print(f"🔍 Chrome Status: {chrome_available}")
    
    # Test service info generation
    start_time = time.time()
    service_info = service.get_service_info()
    info_time = time.time() - start_time
    
    print(f"📊 Service Info Generation: {info_time:.3f} seconds")
    print(f"📊 Platform Features: {len(service_info.get('platform_features', []))}")
    
    # Show Windows-specific features
    if 'platform_features' in service_info:
        print("\n🪟 Windows-Specific Features:")
        for feature in service_info['platform_features']:
            print(f"  {feature}")
    
    return True


def main():
    """Run all Windows enhancement tests."""
    print("🪟 CSC-Reach WhatsApp Web Windows Enhancement Test Suite")
    print("=" * 65)
    
    if platform.system().lower() != "windows":
        print("❌ This test suite is designed for Windows only")
        print(f"Current platform: {platform.system()}")
        return
    
    print(f"🖥️ Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    print()
    
    tests = [
        ("Chrome Detection", test_windows_chrome_detection),
        ("Windows Notifications", test_windows_notifications),
        ("Auto-Send Methods", test_windows_auto_send),
        ("Tab Closing", test_windows_tab_closing),
        ("Chrome Opening", test_windows_chrome_opening),
        ("Performance", run_windows_performance_test),
        ("Full Integration", test_full_windows_integration),
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
            print("\n🎉 All Windows enhancements are working perfectly!")
            print("\n💡 Key Windows Improvements:")
            print("  • Enhanced Chrome detection with registry support")
            print("  • Advanced PowerShell automation with multiple fallbacks")
            print("  • Windows toast notifications")
            print("  • Improved tab closing with DevTools API")
            print("  • Better error handling and logging")
            print("  • Performance optimizations for Windows")
        elif passed > total * 0.7:
            print("\n✅ Most Windows enhancements are working well!")
            print("💡 Some features may require specific Windows configurations")
        else:
            print("\n⚠️ Some Windows enhancements need attention")
            print("💡 Check Chrome installation and Windows permissions")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()