#!/usr/bin/env python3
"""
WhatsApp Multi-Message Template System Demo.

This script demonstrates the key features of the WhatsApp multi-message template system:
- Creating single and multi-message templates
- Different splitting strategies
- Message sequence preview
- Template conversion between modes
- Delivery tracking simulation
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multichannel_messaging.core.whatsapp_multi_message import (
    WhatsAppMultiMessageTemplate,
    MessageSplitStrategy,
    WhatsAppMultiMessageService,
    MessageSequenceRecord
)
from multichannel_messaging.core.whatsapp_multi_message_manager import WhatsAppMultiMessageManager
from multichannel_messaging.core.models import Customer
from unittest.mock import Mock


def print_separator(title: str):
    """Print a section separator."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_template_creation():
    """Demonstrate template creation with different splitting strategies."""
    print_separator("Template Creation Demo")
    
    # Single message template
    print("\n1. Creating Single Message Template:")
    single_template = WhatsAppMultiMessageTemplate(
        id="demo_single",
        name="Welcome Message",
        content="Hello {name}! Welcome to {company}. We're excited to have you join our community and look forward to serving you!",
        multi_message_mode=False
    )
    
    print(f"   Template: {single_template.name}")
    print(f"   Mode: {'Multi-message' if single_template.multi_message_mode else 'Single message'}")
    print(f"   Variables: {single_template.variables}")
    print(f"   Content: {single_template.content}")
    
    # Multi-message template with paragraph splitting
    print("\n2. Creating Multi-Message Template (Paragraph Split):")
    multi_content = """Hello {name}! 👋

Welcome to {company}! We're thrilled to have you join our community.

Our team is here to help you get the most out of our services. If you have any questions, don't hesitate to reach out.

Thank you for choosing us! 🚀"""
    
    multi_template = WhatsAppMultiMessageTemplate(
        id="demo_multi_para",
        name="Multi-Message Welcome",
        content=multi_content,
        multi_message_mode=True,
        split_strategy=MessageSplitStrategy.PARAGRAPH,
        message_delay_seconds=2.0
    )
    
    print(f"   Template: {multi_template.name}")
    print(f"   Mode: {'Multi-message' if multi_template.multi_message_mode else 'Single message'}")
    print(f"   Split Strategy: {multi_template.split_strategy.value}")
    print(f"   Message Count: {len(multi_template.message_sequence)}")
    print(f"   Delay Between Messages: {multi_template.message_delay_seconds}s")
    print(f"   Estimated Send Time: {multi_template.get_estimated_send_time()}s")
    
    for i, message in enumerate(multi_template.message_sequence, 1):
        print(f"   Message {i}: {message}")
    
    # Multi-message template with sentence splitting
    print("\n3. Creating Multi-Message Template (Sentence Split):")
    sentence_content = "Hello {name}! Welcome to our service. We offer amazing features. You'll love our platform. Thank you for joining us!"
    
    sentence_template = WhatsAppMultiMessageTemplate(
        id="demo_multi_sent",
        name="Sentence Split Welcome",
        content=sentence_content,
        multi_message_mode=True,
        split_strategy=MessageSplitStrategy.SENTENCE,
        message_delay_seconds=1.0
    )
    
    print(f"   Template: {sentence_template.name}")
    print(f"   Message Count: {len(sentence_template.message_sequence)}")
    
    for i, message in enumerate(sentence_template.message_sequence, 1):
        print(f"   Message {i}: {message}")
    
    # Custom delimiter splitting
    print("\n4. Creating Multi-Message Template (Custom Split):")
    custom_content = "Welcome {name}!|||Thanks for joining {company}|||We're here to help|||Contact us anytime"
    
    custom_template = WhatsAppMultiMessageTemplate(
        id="demo_multi_custom",
        name="Custom Split Welcome",
        content=custom_content,
        multi_message_mode=True,
        split_strategy=MessageSplitStrategy.CUSTOM,
        custom_split_delimiter="|||",
        message_delay_seconds=1.5
    )
    
    print(f"   Template: {custom_template.name}")
    print(f"   Custom Delimiter: '{custom_template.custom_split_delimiter}'")
    print(f"   Message Count: {len(custom_template.message_sequence)}")
    
    for i, message in enumerate(custom_template.message_sequence, 1):
        print(f"   Message {i}: {message}")
    
    return single_template, multi_template, sentence_template, custom_template


def demo_message_preview():
    """Demonstrate message preview with customer data."""
    print_separator("Message Preview Demo")
    
    # Create sample customer
    customer = Customer(
        name="Alice Johnson",
        company="Tech Innovations Inc",
        phone="+1-555-0123",
        email="alice@techinnovations.com"
    )
    
    print(f"\nSample Customer:")
    print(f"   Name: {customer.name}")
    print(f"   Company: {customer.company}")
    print(f"   Phone: {customer.phone}")
    print(f"   Email: {customer.email}")
    
    # Create template for preview
    template = WhatsAppMultiMessageTemplate(
        id="demo_preview",
        name="Preview Demo",
        content="Hi {name}! 👋\n\nWelcome to {company}!\n\nWe're excited to work with you.",
        multi_message_mode=True,
        split_strategy=MessageSplitStrategy.PARAGRAPH
    )
    
    print(f"\nTemplate: {template.name}")
    print(f"Original Content:\n{template.content}")
    
    # Preview with customer data
    customer_data = customer.to_dict()
    rendered_messages = template.preview_message_sequence(customer_data)
    
    print(f"\nRendered Messages for {customer.name}:")
    for i, message in enumerate(rendered_messages, 1):
        print(f"   Message {i}: {message}")
        if i < len(rendered_messages):
            print(f"   [Delay: {template.message_delay_seconds}s]")


def demo_template_conversion():
    """Demonstrate converting between single and multi-message modes."""
    print_separator("Template Conversion Demo")
    
    # Start with single message
    original_content = "Hello {name}! Welcome to {company}. We're excited to have you join us. Our team is here to help you succeed. Thank you for choosing our services!"
    
    template = WhatsAppMultiMessageTemplate(
        id="demo_convert",
        name="Conversion Demo",
        content=original_content,
        multi_message_mode=False
    )
    
    print(f"\n1. Original Single Message Template:")
    print(f"   Content: {template.content}")
    print(f"   Mode: {'Multi-message' if template.multi_message_mode else 'Single message'}")
    
    # Convert to multi-message
    print(f"\n2. Converting to Multi-Message Mode:")
    multi_messages = template.convert_to_multi_message()
    
    print(f"   Mode: {'Multi-message' if template.multi_message_mode else 'Single message'}")
    print(f"   Message Count: {len(multi_messages)}")
    
    for i, message in enumerate(multi_messages, 1):
        print(f"   Message {i}: {message}")
    
    # Convert back to single message
    print(f"\n3. Converting Back to Single Message:")
    single_content = template.convert_to_single_message()
    template.multi_message_mode = False
    
    print(f"   Mode: {'Multi-message' if template.multi_message_mode else 'Single message'}")
    print(f"   Content: {single_content}")


def demo_template_validation():
    """Demonstrate template validation."""
    print_separator("Template Validation Demo")
    
    # Valid template
    print("\n1. Valid Template:")
    valid_template = WhatsAppMultiMessageTemplate(
        id="demo_valid",
        name="Valid Template",
        content="Hello {name}!\n\nWelcome to our service!",
        multi_message_mode=True,
        split_strategy=MessageSplitStrategy.PARAGRAPH,
        message_delay_seconds=1.0
    )
    
    errors = valid_template.validate_message_sequence()
    print(f"   Template: {valid_template.name}")
    print(f"   Validation Result: {'✅ Valid' if not errors else '❌ Invalid'}")
    if errors:
        for error in errors:
            print(f"   Error: {error}")
    
    # Invalid template - empty content
    print("\n2. Invalid Template (Empty Content):")
    invalid_template = WhatsAppMultiMessageTemplate(
        id="demo_invalid",
        name="Invalid Template",
        content="",
        multi_message_mode=True
    )
    
    errors = invalid_template.validate_message_sequence()
    print(f"   Template: {invalid_template.name}")
    print(f"   Validation Result: {'✅ Valid' if not errors else '❌ Invalid'}")
    if errors:
        for error in errors:
            print(f"   Error: {error}")
    
    # Invalid template - delay too short
    print("\n3. Invalid Template (Delay Too Short):")
    invalid_delay_template = WhatsAppMultiMessageTemplate(
        id="demo_invalid_delay",
        name="Invalid Delay Template",
        content="Valid content here",
        multi_message_mode=True,
        message_delay_seconds=0.05  # Too short
    )
    
    errors = invalid_delay_template.validate_message_sequence()
    print(f"   Template: {invalid_delay_template.name}")
    print(f"   Delay: {invalid_delay_template.message_delay_seconds}s")
    print(f"   Validation Result: {'✅ Valid' if not errors else '❌ Invalid'}")
    if errors:
        for error in errors:
            print(f"   Error: {error}")


def demo_manager_functionality():
    """Demonstrate template manager functionality."""
    print_separator("Template Manager Demo")
    
    # Create mock config manager
    from unittest.mock import Mock
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = Mock()
        config_manager.get_user_data_dir.return_value = temp_dir
        
        # Create manager
        manager = WhatsAppMultiMessageManager(config_manager)
        
        print(f"\n1. Creating Template Manager:")
        print(f"   Storage Path: {manager.storage_path}")
        print(f"   Initial Template Count: {len(manager.get_all_templates())}")
        
        # Create templates
        print(f"\n2. Creating Templates:")
        
        template1 = manager.create_template(
            name="Welcome Message",
            content="Hello {name}!\n\nWelcome to {company}!",
            multi_message_mode=True,
            split_strategy=MessageSplitStrategy.PARAGRAPH
        )
        print(f"   Created: {template1.name}")
        
        template2 = manager.create_template(
            name="Follow Up",
            content="Hi {name}, just following up on your inquiry about our services.",
            multi_message_mode=False
        )
        print(f"   Created: {template2.name}")
        
        template3 = manager.create_template(
            name="Bienvenido",
            content="¡Hola {name}!\n\n¡Bienvenido a {company}!",
            language="es",
            multi_message_mode=True
        )
        print(f"   Created: {template3.name}")
        
        # List templates
        print(f"\n3. Template Inventory:")
        all_templates = manager.get_all_templates()
        print(f"   Total Templates: {len(all_templates)}")
        
        for template in all_templates:
            mode = "Multi" if template.multi_message_mode else "Single"
            msg_count = len(template.message_sequence) if template.multi_message_mode else 1
            print(f"   - {template.name} ({template.language}) - {mode} mode - {msg_count} messages")
        
        # Search templates
        print(f"\n4. Search Functionality:")
        welcome_templates = manager.search_templates("welcome")
        print(f"   Search 'welcome': {len(welcome_templates)} results")
        for template in welcome_templates:
            print(f"   - {template.name}")
        
        # Filter by language
        english_templates = manager.get_templates_by_language("en")
        spanish_templates = manager.get_templates_by_language("es")
        print(f"   English templates: {len(english_templates)}")
        print(f"   Spanish templates: {len(spanish_templates)}")
        
        # Export/Import
        print(f"\n5. Export/Import:")
        export_data = manager.export_templates()
        print(f"   Exported {export_data['template_count']} templates")
        
        # Clear and import
        for template in all_templates:
            manager.delete_template(template.id)
        print(f"   Cleared all templates: {len(manager.get_all_templates())} remaining")
        
        imported = manager.import_templates(export_data)
        print(f"   Imported {len(imported)} templates")
        print(f"   Final count: {len(manager.get_all_templates())} templates")


def demo_service_simulation():
    """Demonstrate multi-message service with simulation."""
    print_separator("Multi-Message Service Demo")
    
    # Create mock WhatsApp service
    mock_whatsapp_service = Mock()
    service = WhatsAppMultiMessageService(mock_whatsapp_service)
    
    # Mock successful message sending
    service._send_individual_message = Mock(return_value=True)
    
    print(f"\n1. Service Setup:")
    print(f"   Active Sequences: {len(service.active_sequences)}")
    
    # Create customer and template
    customer = Customer(
        name="Bob Wilson",
        company="Wilson Enterprises",
        phone="+1-555-0456",
        email="bob@wilson.com"
    )
    
    template = WhatsAppMultiMessageTemplate(
        id="demo_service",
        name="Service Demo",
        content="Hi {name}! 👋\n\nThanks for contacting {company}.\n\nWe'll get back to you soon!",
        multi_message_mode=True,
        split_strategy=MessageSplitStrategy.PARAGRAPH,
        message_delay_seconds=0.1  # Fast for demo
    )
    
    print(f"\n2. Sending Multi-Message Sequence:")
    print(f"   Customer: {customer.name}")
    print(f"   Template: {template.name}")
    print(f"   Messages to Send: {len(template.message_sequence)}")
    
    # Track progress
    progress_updates = []
    def progress_callback(sequence_record):
        progress_updates.append({
            'progress': sequence_record.get_progress_percentage(),
            'sent': sequence_record.messages_sent,
            'failed': sequence_record.messages_failed
        })
        print(f"   Progress: {sequence_record.get_progress_percentage():.1f}% "
              f"(Sent: {sequence_record.messages_sent}, Failed: {sequence_record.messages_failed})")
    
    # Send sequence
    print(f"\n3. Sending Messages:")
    sequence_record = service.send_multi_message_sequence(
        customer=customer,
        template=template,
        progress_callback=progress_callback
    )
    
    print(f"\n4. Final Results:")
    print(f"   Sequence ID: {sequence_record.sequence_id}")
    print(f"   Status: {sequence_record.status.value}")
    print(f"   Total Messages: {len(sequence_record.message_records)}")
    print(f"   Successful: {sequence_record.get_success_count()}")
    print(f"   Failed: {sequence_record.get_failure_count()}")
    print(f"   Progress Updates: {len(progress_updates)}")
    
    # Show individual message results
    print(f"\n5. Individual Message Results:")
    for i, record in enumerate(sequence_record.message_records, 1):
        content = record.rendered_content.get("whatsapp_content", "")[:50] + "..."
        print(f"   Message {i}: {record.status.value} - {content}")


def main():
    """Run all demos."""
    print("WhatsApp Multi-Message Template System Demo")
    print("=" * 60)
    print("This demo showcases the key features of the WhatsApp multi-message system:")
    print("- Template creation with different splitting strategies")
    print("- Message preview with customer data")
    print("- Template conversion between modes")
    print("- Validation and error handling")
    print("- Template management and persistence")
    print("- Multi-message service simulation")
    
    try:
        # Run demos
        templates = demo_template_creation()
        demo_message_preview()
        demo_template_conversion()
        demo_template_validation()
        demo_manager_functionality()
        demo_service_simulation()
        
        print_separator("Demo Complete")
        print("\n✅ All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("- ✅ Single and multi-message template creation")
        print("- ✅ Multiple splitting strategies (paragraph, sentence, custom)")
        print("- ✅ Message preview with variable substitution")
        print("- ✅ Template mode conversion")
        print("- ✅ Comprehensive validation")
        print("- ✅ Template management (CRUD operations)")
        print("- ✅ Search and filtering")
        print("- ✅ Export/import functionality")
        print("- ✅ Multi-message service with progress tracking")
        print("- ✅ Delivery status simulation")
        
        print("\nThe WhatsApp Multi-Message Template System is ready for use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())