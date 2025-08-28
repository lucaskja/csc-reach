# API Reference

## Overview

CSC-Reach provides internal APIs for component communication and extensibility. While primarily a desktop application, it exposes well-defined interfaces for template management, data processing, and service integration.

## Core APIs

### Template Management API

#### TemplateManager Class

**Location**: `src/multichannel_messaging/core/template_manager.py`

```python
class TemplateManager:
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new message template"""
        
    def get_template(self, template_id: str) -> MessageTemplate:
        """Retrieve template by ID"""
        
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing template"""
        
    def delete_template(self, template_id: str) -> bool:
        """Delete template"""
        
    def list_templates(self, category: str = None) -> List[MessageTemplate]:
        """List all templates, optionally filtered by category"""
        
    def search_templates(self, query: str) -> List[MessageTemplate]:
        """Search templates by name or content"""
```

#### Template Data Structure

```python
@dataclass
class MessageTemplate:
    id: str
    name: str
    category: str
    subject: str
    content: str
    variables: List[str]
    channel: str  # "email", "whatsapp", "both"
    created_at: datetime
    updated_at: datetime
    usage_count: int
```

### Data Processing API

#### CSVProcessor Class

**Location**: `src/multichannel_messaging/core/csv_processor.py`

```python
class CSVProcessor:
    def process_file(self, file_path: str) -> ProcessingResult:
        """Process any supported file format"""
        
    def detect_format(self, file_path: str) -> str:
        """Auto-detect file format"""
        
    def detect_encoding(self, file_path: str) -> str:
        """Auto-detect file encoding"""
        
    def validate_data(self, data: List[Dict]) -> ValidationResult:
        """Validate processed data"""
        
    def map_columns(self, data: List[Dict], mapping: Dict[str, str]) -> List[Customer]:
        """Map columns to Customer objects"""
```

#### Data Structures

```python
@dataclass
class Customer:
    name: str
    company: str
    phone: str
    email: str
    whatsapp_opt_in: bool = True
    preferred_channel: str = "both"
    
@dataclass
class ProcessingResult:
    success: bool
    data: List[Customer]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
```

### Configuration API

#### ConfigManager Class

**Location**: `src/multichannel_messaging/core/config_manager.py`

```python
class ConfigManager:
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file"""
        
    def save_config(self, config_path: str = None) -> bool:
        """Save current configuration to file"""
        
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema"""
```

### Message Logging API

#### MessageLogger Class

**Location**: `src/multichannel_messaging/core/message_logger.py`

```python
class MessageLogger:
    def log_message_sent(self, customer: Customer, channel: str, 
                        status: str, details: Dict = None) -> bool:
        """Log message sending attempt"""
        
    def get_logs(self, start_date: datetime = None, 
                end_date: datetime = None) -> List[MessageLog]:
        """Retrieve message logs"""
        
    def get_analytics(self, date_range: Tuple[datetime, datetime]) -> AnalyticsData:
        """Generate analytics report"""
        
    def export_logs(self, format: str = "csv", file_path: str = None) -> str:
        """Export logs in specified format"""
```

## Service Integration APIs

### Email Service API

#### Abstract Base Class

```python
from abc import ABC, abstractmethod

class EmailService(ABC):
    @abstractmethod
    def send_email(self, subject: str, body: str, recipient: str, 
                  attachments: List[str] = None) -> SendResult:
        """Send email through platform-specific implementation"""
        
    @abstractmethod
    def create_draft(self, subject: str, body: str, recipient: str) -> bool:
        """Create draft email for review"""
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if email service is available"""
```

#### Platform Implementations

**Windows Outlook Service**:
```python
class OutlookWindowsService(EmailService):
    def send_email(self, subject: str, body: str, recipient: str, 
                  attachments: List[str] = None) -> SendResult:
        """Send email using Windows COM automation"""
        
    def create_draft(self, subject: str, body: str, recipient: str) -> bool:
        """Create draft using COM interface"""
```

**macOS Outlook Service**:
```python
class OutlookMacOSService(EmailService):
    def send_email(self, subject: str, body: str, recipient: str, 
                  attachments: List[str] = None) -> SendResult:
        """Send email using AppleScript automation"""
        
    def create_draft(self, subject: str, body: str, recipient: str) -> bool:
        """Create draft using AppleScript"""
```

### WhatsApp Service API

#### WhatsAppWebService Class

```python
class WhatsAppWebService:
    def send_message(self, phone: str, message: str) -> SendResult:
        """Send WhatsApp message via web automation"""
        
    def send_multiple_messages(self, phone: str, messages: List[str]) -> List[SendResult]:
        """Send multiple messages to same contact"""
        
    def is_logged_in(self) -> bool:
        """Check if WhatsApp Web is logged in"""
        
    def wait_for_login(self, timeout: int = 60) -> bool:
        """Wait for user to log in to WhatsApp Web"""
```

## Endpoints

### Internal Event System

CSC-Reach uses an internal event system for component communication:

#### Event Types

```python
class EventType(Enum):
    # Data Events
    DATA_IMPORTED = "data_imported"
    DATA_VALIDATED = "data_validated"
    
    # Template Events
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    
    # Message Events
    MESSAGE_SENT = "message_sent"
    MESSAGE_FAILED = "message_failed"
    
    # Progress Events
    PROGRESS_UPDATED = "progress_updated"
    OPERATION_COMPLETED = "operation_completed"
    
    # Configuration Events
    CONFIG_CHANGED = "config_changed"
    THEME_CHANGED = "theme_changed"
    LANGUAGE_CHANGED = "language_changed"
```

#### Event Manager

```python
class EventManager:
    def subscribe(self, event_type: EventType, callback: Callable) -> str:
        """Subscribe to event type"""
        
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        
    def emit(self, event_type: EventType, data: Dict = None) -> bool:
        """Emit event to all subscribers"""
        
    def emit_async(self, event_type: EventType, data: Dict = None) -> bool:
        """Emit event asynchronously"""
```

### Plugin System API (Future)

#### Plugin Interface

```python
class PluginInterface(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name"""
        
    @abstractmethod
    def get_version(self) -> str:
        """Get plugin version"""
        
    @abstractmethod
    def initialize(self, app_context: ApplicationContext) -> bool:
        """Initialize plugin"""
        
    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown plugin"""
```

## Authentication

### Local Authentication

CSC-Reach operates as a local desktop application and doesn't require traditional authentication. However, it manages authentication for external services:

#### Outlook Authentication
- **Windows**: Uses current user's Outlook profile automatically
- **macOS**: Requires automation permissions granted by user

#### WhatsApp Authentication
- **Web-based**: User must scan QR code in WhatsApp Web
- **Session Management**: Maintains session across application restarts

### Permission Management

#### macOS Permissions
```python
class PermissionManager:
    def check_automation_permission(self) -> bool:
        """Check if automation permission is granted"""
        
    def request_automation_permission(self) -> bool:
        """Request automation permission from user"""
        
    def check_accessibility_permission(self) -> bool:
        """Check if accessibility permission is granted"""
```

## Error Handling

### Error Response Format

All API methods return structured error information:

```python
@dataclass
class APIResult:
    success: bool
    data: Any = None
    error_code: str = None
    error_message: str = None
    details: Dict[str, Any] = None
```

### Error Codes

#### Template Management Errors
- `TEMPLATE_NOT_FOUND`: Template with specified ID not found
- `TEMPLATE_VALIDATION_ERROR`: Template data validation failed
- `TEMPLATE_DUPLICATE_NAME`: Template name already exists
- `TEMPLATE_CATEGORY_INVALID`: Invalid template category

#### Data Processing Errors
- `FILE_NOT_FOUND`: Specified file does not exist
- `FILE_FORMAT_UNSUPPORTED`: File format not supported
- `FILE_ENCODING_ERROR`: Cannot detect or decode file encoding
- `DATA_VALIDATION_ERROR`: Customer data validation failed
- `COLUMN_MAPPING_ERROR`: Cannot map columns to required fields

#### Service Integration Errors
- `OUTLOOK_NOT_AVAILABLE`: Microsoft Outlook not installed or accessible
- `OUTLOOK_PERMISSION_DENIED`: Automation permission not granted
- `WHATSAPP_NOT_LOGGED_IN`: WhatsApp Web not logged in
- `WHATSAPP_CONNECTION_ERROR`: Cannot connect to WhatsApp Web

#### Configuration Errors
- `CONFIG_FILE_NOT_FOUND`: Configuration file not found
- `CONFIG_VALIDATION_ERROR`: Configuration validation failed
- `CONFIG_PERMISSION_ERROR`: Cannot write to configuration directory

### Error Recovery

#### Automatic Recovery
- **Retry Logic**: Automatic retries for transient failures
- **Fallback Options**: Alternative approaches when primary method fails
- **State Recovery**: Restore application state after errors

#### User-Guided Recovery
- **Error Dialogs**: Clear error messages with suggested actions
- **Diagnostic Tools**: Built-in diagnostic utilities
- **Help Integration**: Context-sensitive help for error resolution

## Usage Examples

### Template Management Example

```python
# Initialize template manager
template_manager = TemplateManager()

# Create new template
template_data = {
    "name": "Welcome Email",
    "category": "Welcome",
    "subject": "Welcome to {company}!",
    "content": "Hello {name}, welcome to our service!",
    "channel": "email"
}

result = template_manager.create_template(template_data)
if result.success:
    template_id = result.data
    print(f"Template created with ID: {template_id}")
else:
    print(f"Error: {result.error_message}")
```

### Data Processing Example

```python
# Initialize CSV processor
processor = CSVProcessor()

# Process customer data file
result = processor.process_file("customers.csv")
if result.success:
    customers = result.data
    print(f"Processed {len(customers)} customers")
    
    # Validate data
    validation = processor.validate_data(customers)
    if validation.success:
        print("Data validation passed")
    else:
        print(f"Validation errors: {validation.errors}")
else:
    print(f"Processing failed: {result.error_message}")
```

### Message Sending Example

```python
# Initialize email service
email_service = OutlookWindowsService()  # or OutlookMacOSService()

# Send personalized email
if email_service.is_available():
    result = email_service.send_email(
        subject="Welcome to CSC-Reach!",
        body="Hello John, thank you for joining us!",
        recipient="john@example.com"
    )
    
    if result.success:
        print("Email sent successfully")
    else:
        print(f"Failed to send email: {result.error_message}")
else:
    print("Email service not available")
```
