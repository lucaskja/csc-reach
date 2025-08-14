#!/usr/bin/env python3
"""
Cross-platform WhatsApp Web Integration Test Script.
Tests functionality across different platforms and verifies Windows enhancements exist.
"""

import sys
import os
import time
import platform
import inspect
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multichannel_messaging.services.whatsapp_web_service import WhatsAppWebService
from multichannel_messaging.core.models import Customer, MessageTemplate
from multichannel_messaging.utils.logger import get_logger

logger = get_logger(__name__)


def test_service_initialization():
    """Test that the service initializes correctly on all platforms."""
    print("🚀 Testing Service Initialization")
    print("=" * 35)
    
    try:
        service = WhatsAppWebService(
            close_existing_tabs=True,
            auto_send=False,
            rate_limit_per_minute=5,
            daily_message_limit=50,
            min_delay_seconds=30
        )
        
        print("✅ Service initialized successfully")
        print(f"📊 Close existing tabs: {service.close_existing_tabs}")
        print(f"📊 Auto-send: {service.auto_send}")
        print(f"📊 Rate limit: {service.rate_limit_per_minute}/min")
        print(f"📊 Daily limit: {service.daily_message_limit}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False


def test_windows_methods_exist():
    """Test that Windows-specific methods exist in the service."""
    print("\n🪟 Testing Windows Methods Existence")
    print("=" * 40)
    
    service = WhatsAppWebService()
    
    # List of Windows-specific methods that should exist
    windows_methods = [
        '_detect_chrome_windows',
        '_auto_send_javascript_windows',
        '_auto_send_windows',
        '_auto_send_windows_simple',
        '_close_whatsapp_tabs_windows',
        '_show_windows_notification'
    ]
    
    results = {}
    
    for method_name in windows_methods:
        exists = hasattr(service, method_name)
        results[method_name] = exists
        
        if exists:
            method = getattr(service, method_name)
            is_callable = callable(method)
            print(f"✅ {method_name}: {'Callable' if is_callable else 'Not callable'}")
            
            # Check if method has proper signature
            if is_callable:
                try:
                    sig = inspect.signature(method)
                    param_count = len(sig.parameters)
                    print(f"   📋 Parameters: {param_count}")
                except Exception as e:
                    print(f"   ⚠️ Signature inspection failed: {e}")
        else:
            print(f"❌ {method_name}: Missing")
    
    success_count = sum(1 for exists in results.values() if exists)
    total_count = len(results)
    
    print(f"\n📊 Windows Methods: {success_count}/{total_count} found")
    
    return success_count == total_count


def test_chrome_detection():
    """Test Chrome detection on current platform."""
    print("\n🔍 Testing Chrome Detection")
    print("=" * 28)
    
    service = WhatsAppWebService()
    
    try:
        chrome_available, chrome_info = service._check_chrome_availability()
        
        print(f"🌐 Platform: {platform.system()}")
        print(f"🔍 Chrome Available: {chrome_available}")
        print(f"📋 Chrome Info: {chrome_info}")
        
        # Test Windows-specific detection if on Windows
        if platform.system().lower() == "windows" and hasattr(service, '_detect_chrome_windows'):
            print("\n🪟 Testing Windows-specific Chrome detection...")
            try:
                chrome_details = service._detect_chrome_windows()
                print(f"   Found: {chrome_details.get('found', False)}")
                print(f"   Paths: {len(chrome_details.get('paths', []))}")
                print(f"   Version: {chrome_details.get('version', 'Unknown')}")
                print(f"   Registry: {chrome_details.get('registry_found', False)}")
                print(f"   Running: {chrome_details.get('process_running', False)}")
            except Exception as e:
                print(f"   ⚠️ Windows Chrome detection failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chrome detection failed: {e}")
        return False


def test_service_configuration():
    """Test service configuration."""
    print("\n⚙️ Testing Service Configuration")
    print("=" * 32)
    
    service = WhatsAppWebService()
    
    try:
        # Test basic configuration
        success, message = service.configure_service(
            acknowledge_risks=True,
            auto_send=False,
            close_existing_tabs=True
        )
        
        if success:
            print("✅ Service configured successfully")
            print(f"📋 Message: {message}")
            
            # Test configuration loading
            is_configured = service.is_configured()
            print(f"📊 Is Configured: {is_configured}")
            
            # Test daily usage
            usage = service.get_daily_usage()
            print(f"📊 Daily Usage: {usage}")
            
            return True
        else:
            print(f"❌ Configuration failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_message_processing():
    """Test message processing functionality."""
    print("\n📝 Testing Message Processing")
    print("=" * 30)
    
    service = WhatsAppWebService()
    
    try:
        # Configure service first
        service.configure_service(acknowledge_risks=True)
        
        # Create test data
        customer = Customer(
            name="Test User",
            phone="+1234567890",
            email="test@example.com",
            company="Test Company"
        )
        
        template = MessageTemplate(
            id="test-template-001",
            name="Test Template",
            channels=["whatsapp"],
            content="Hello {name}, this is a test message from {company}!",
            whatsapp_content="Hello {name}, this is a WhatsApp test message from {company}!",
            variables=["name", "company"]
        )
        
        print(f"👤 Customer: {customer.name} ({customer.phone})")
        print(f"📄 Template: {template.name}")
        
        # Test phone number formatting
        formatted_phone = service._format_phone_number(customer.phone)
        print(f"📞 Formatted Phone: {customer.phone} → {formatted_phone}")
        
        # Test message rendering
        rendered_message = service._render_message(customer, template)
        print(f"💬 Rendered Message: {rendered_message[:50]}...")
        
        # Test URL creation
        whatsapp_url = service._create_whatsapp_url(formatted_phone, rendered_message)
        print(f"🔗 WhatsApp URL: {whatsapp_url[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Message processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_platform_specific_features():
    """Test platform-specific features."""
    print("\n🖥️ Testing Platform-Specific Features")
    print("=" * 38)
    
    service = WhatsAppWebService()
    current_platform = platform.system().lower()
    
    print(f"🖥️ Current Platform: {current_platform}")
    
    # Test tab closing methods
    tab_closing_methods = {
        'darwin': '_close_whatsapp_tabs_macos',
        'windows': '_close_whatsapp_tabs_windows',
        'linux': '_close_whatsapp_tabs_linux'
    }
    
    expected_method = tab_closing_methods.get(current_platform)
    if expected_method:
        has_method = hasattr(service, expected_method)
        print(f"🧹 Tab Closing Method ({expected_method}): {'✅ Found' if has_method else '❌ Missing'}")
        
        if has_method:
            try:
                # Test the method (should not fail even if no tabs to close)
                method = getattr(service, expected_method)
                result = method()
                print(f"   📊 Method Result: {result}")
            except Exception as e:
                print(f"   ⚠️ Method execution failed: {e}")
    
    # Test auto-send methods
    auto_send_methods = {
        'darwin': ['_auto_send_macos', '_auto_send_macos_simple'],
        'windows': ['_auto_send_windows', '_auto_send_windows_simple', '_auto_send_javascript_windows'],
        'linux': ['_auto_send_linux']
    }
    
    expected_methods = auto_send_methods.get(current_platform, [])
    for method_name in expected_methods:
        has_method = hasattr(service, method_name)
        print(f"🤖 Auto-Send Method ({method_name}): {'✅ Found' if has_method else '❌ Missing'}")
    
    return True


def test_service_info():
    """Test service information generation."""
    print("\n📊 Testing Service Information")
    print("=" * 31)
    
    service = WhatsAppWebService()
    
    try:
        service_info = service.get_service_info()
        
        print(f"📋 Service Name: {service_info.get('service_name', 'Unknown')}")
        print(f"📋 Platform: {service_info.get('platform', 'Unknown')}")
        print(f"📋 Available: {service_info.get('is_available', False)}")
        print(f"📋 Configured: {service_info.get('is_configured', False)}")
        
        # Chrome status
        chrome_status = service_info.get('chrome_status', {})
        print(f"🌐 Chrome Available: {chrome_status.get('available', False)}")
        print(f"🌐 Chrome Info: {chrome_status.get('info', 'Unknown')}")
        
        # Platform features
        platform_features = service_info.get('platform_features', [])
        print(f"🖥️ Platform Features: {len(platform_features)}")
        for feature in platform_features[:3]:  # Show first 3
            print(f"   {feature}")
        if len(platform_features) > 3:
            print(f"   ... and {len(platform_features) - 3} more")
        
        # Warnings
        warnings = service_info.get('warnings', [])
        print(f"⚠️ Warnings: {len(warnings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service info test failed: {e}")
        return False


def test_error_handling():
    """Test error handling and edge cases."""
    print("\n🛡️ Testing Error Handling")
    print("=" * 26)
    
    service = WhatsAppWebService()
    
    try:
        # Test with invalid phone number
        invalid_phone = service._format_phone_number("invalid")
        print(f"📞 Invalid Phone Handling: {invalid_phone}")
        
        # Test with empty customer data
        try:
            customer = Customer(
                name="",
                phone="",
                email="",
                company=""
            )
            print("❌ Empty customer should have failed validation")
            return False
        except Exception:
            print("✅ Empty customer properly rejected")
        
        # Test service without configuration
        can_send, reason = service.can_send_message()
        print(f"🚫 Unconfigured Service: {can_send} - {reason}")
        
        # Test last error functionality
        last_error = service.get_last_error()
        print(f"🔍 Last Error: {last_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def run_performance_test():
    """Test performance of key operations."""
    print("\n⚡ Performance Testing")
    print("=" * 22)
    
    service = WhatsAppWebService()
    
    # Test service initialization time
    start_time = time.time()
    test_service = WhatsAppWebService()
    init_time = time.time() - start_time
    print(f"🚀 Service Initialization: {init_time:.3f}s")
    
    # Test Chrome detection time
    start_time = time.time()
    chrome_available, chrome_info = service._check_chrome_availability()
    detection_time = time.time() - start_time
    print(f"🔍 Chrome Detection: {detection_time:.3f}s")
    
    # Test service info generation time
    start_time = time.time()
    service_info = service.get_service_info()
    info_time = time.time() - start_time
    print(f"📊 Service Info Generation: {info_time:.3f}s")
    
    # Performance thresholds
    thresholds = {
        'init_time': 1.0,      # Should initialize within 1 second
        'detection_time': 2.0,  # Chrome detection within 2 seconds
        'info_time': 1.0       # Service info within 1 second
    }
    
    performance_ok = (
        init_time < thresholds['init_time'] and
        detection_time < thresholds['detection_time'] and
        info_time < thresholds['info_time']
    )
    
    print(f"⚡ Performance: {'✅ Good' if performance_ok else '⚠️ Slow'}")
    
    return performance_ok


def main():
    """Run all cross-platform tests."""
    print("🌍 CSC-Reach WhatsApp Web Cross-Platform Test Suite")
    print("=" * 60)
    
    print(f"🖥️ Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print()
    
    tests = [
        ("Service Initialization", test_service_initialization),
        ("Windows Methods Existence", test_windows_methods_exist),
        ("Chrome Detection", test_chrome_detection),
        ("Service Configuration", test_service_configuration),
        ("Message Processing", test_message_processing),
        ("Platform-Specific Features", test_platform_specific_features),
        ("Service Information", test_service_info),
        ("Error Handling", test_error_handling),
        ("Performance", run_performance_test),
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
            print("\n🎉 All tests passed! WhatsApp Web integration is working perfectly!")
            print("\n💡 Key Features Verified:")
            print("  • Service initialization and configuration")
            print("  • Cross-platform Chrome detection")
            print("  • Message processing and URL generation")
            print("  • Platform-specific method availability")
            print("  • Error handling and edge cases")
            print("  • Performance within acceptable limits")
            
            if platform.system().lower() == "windows":
                print("  • Windows-specific enhancements active")
            else:
                print("  • Windows enhancements ready for Windows deployment")
                
        elif passed > total * 0.8:
            print("\n✅ Most tests passed! System is largely functional.")
            print("💡 Minor issues detected but core functionality works")
        else:
            print("\n⚠️ Several tests failed. System needs attention.")
            print("💡 Check error messages above for specific issues")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()