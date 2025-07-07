# Multi-Channel Bulk Messaging System - Design Document

## Architecture Overview

The application follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│              GUI Layer                  │
│  (PySide6 - Main Window, Dialogs)      │
├─────────────────────────────────────────┤
│            Business Logic               │
│  (Core Models, Validators, Managers)    │
├─────────────────────────────────────────┤
│            Service Layer                │
│  (WhatsApp API, Outlook Integration)    │
├─────────────────────────────────────────┤
│            Utility Layer                │
│  (CSV Processing, Logging, Config)      │
└─────────────────────────────────────────┘
```

## Module Structure

### GUI Layer (`src/multichannel_messaging/gui/`)
- **main_window.py**: Main application window with tabbed interface
- **csv_import_dialog.py**: CSV file import and validation dialog
- **template_editor.py**: Message template editing interface
- **settings_dialog.py**: Application configuration dialog
- **progress_dialog.py**: Sending progress and status display
- **report_viewer.py**: Sending reports and history viewer
- **widgets/**: Custom UI components and widgets

### Core Layer (`src/multichannel_messaging/core/`)
- **models.py**: Data models (Customer, Message, Template, etc.)
- **config_manager.py**: Configuration management and persistence
- **quota_manager.py**: Daily quota tracking and enforcement
- **message_manager.py**: Message composition and validation
- **csv_processor.py**: CSV file parsing and validation
- **validators.py**: Data validation utilities

### Services Layer (`src/multichannel_messaging/services/`)
- **whatsapp_service.py**: WhatsApp Business API integration
- **email_service.py**: Outlook integration (platform-specific)
- **outlook_windows.py**: Windows Outlook COM integration
- **outlook_macos.py**: macOS Outlook AppleScript integration
- **api_client.py**: Base API client with retry logic

### Utils Layer (`src/multichannel_messaging/utils/`)
- **logger.py**: Logging configuration and utilities
- **exceptions.py**: Custom exception classes
- **helpers.py**: General utility functions
- **platform_utils.py**: Platform-specific utilities

### Localization (`src/multichannel_messaging/localization/`)
- **translator.py**: Translation management
- **messages_en.py**: English translations
- **messages_pt.py**: Portuguese translations
- **messages_es.py**: Spanish translations

## Data Models

### Customer Model
```python
@dataclass
class Customer:
    name: str
    company: str
    phone: str
    email: str
    
    def validate(self) -> bool
    def to_dict(self) -> dict
```

### Message Template Model
```python
@dataclass
class MessageTemplate:
    id: str
    name: str
    channel: str  # 'email' or 'whatsapp'
    subject: str  # for email only
    content: str
    language: str
    variables: List[str]
    
    def render(self, customer: Customer) -> str
```

### Sending Report Model
```python
@dataclass
class SendingReport:
    timestamp: datetime
    channel: str
    total_recipients: int
    successful_sends: int
    failed_sends: int
    errors: List[str]
```

## User Interface Design

### Main Window Layout
```
┌─────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help                          │
├─────────────────────────────────────────────────────────┤
│ [Import CSV] [Templates] [Settings] [Send] [Reports]    │
├─────────────────────────────────────────────────────────┤
│ ┌─ Recipients ─┐ ┌─ Message Preview ─┐ ┌─ Status ─┐    │
│ │              │ │                   │ │          │    │
│ │ Customer     │ │ Email Template:   │ │ Ready    │    │
│ │ List         │ │ [Template Name]   │ │          │    │
│ │              │ │                   │ │ Quota:   │    │
│ │ [✓] John Doe │ │ Subject: ...      │ │ 95/100   │    │
│ │ [✓] Jane...  │ │ Content: ...      │ │          │    │
│ │              │ │                   │ │          │    │
│ │              │ │ WhatsApp Template:│ │          │    │
│ │              │ │ [Template Name]   │ │          │    │
│ │              │ │ Content: ...      │ │          │    │
│ └──────────────┘ └───────────────────┘ └──────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Key UI Components

1. **Tabbed Interface**: Separate tabs for different functions
2. **Recipient List**: Checkable list with customer data preview
3. **Template Selector**: Dropdown with preview pane
4. **Progress Indicators**: Real-time sending status
5. **Status Bar**: Current quota, connection status, etc.

## Service Integration Design

### WhatsApp Business API Integration
```python
class WhatsAppService:
    def __init__(self, api_key: str, phone_number_id: str)
    def send_message(self, recipient: str, message: str) -> bool
    def validate_credentials(self) -> bool
    def get_rate_limits(self) -> dict
```

### Outlook Integration
```python
class EmailService:
    def send_bulk_email(self, recipients: List[Customer], template: MessageTemplate) -> SendingReport
    def validate_outlook_connection(self) -> bool
    def create_mail_merge(self, template: MessageTemplate, recipients: List[Customer]) -> bool
```

## Configuration Management

### Configuration Structure
```yaml
app:
  language: "en"
  theme: "system"
  auto_save: true

whatsapp:
  api_key: ""
  phone_number_id: ""
  webhook_url: ""

email:
  outlook_profile: "default"
  signature_include: true

quotas:
  daily_limit: 100
  reset_time: "00:00"

templates:
  default_email: "welcome_email"
  default_whatsapp: "welcome_whatsapp"
```

## Error Handling Strategy

### Error Categories
1. **User Input Errors**: Invalid CSV format, missing data
2. **Configuration Errors**: Missing API keys, invalid settings
3. **Service Errors**: API failures, network issues
4. **System Errors**: File permissions, memory issues

### Error Handling Approach
- Graceful degradation for non-critical errors
- Clear user-facing error messages
- Detailed logging for debugging
- Retry mechanisms for transient failures
- Rollback capabilities for batch operations

## Security Considerations

### Data Protection
- API credentials encrypted at rest
- No persistent storage of customer data
- Secure communication with external APIs
- Input validation and sanitization

### Privacy Compliance
- Minimal data collection
- Clear data usage policies
- User consent for data processing
- Right to data deletion

## Performance Optimization

### Key Performance Areas
1. **CSV Processing**: Streaming for large files
2. **UI Responsiveness**: Background threading for long operations
3. **Memory Management**: Efficient data structures
4. **API Rate Limiting**: Intelligent batching and throttling

### Scalability Considerations
- Configurable batch sizes
- Asynchronous message sending
- Progress tracking and cancellation
- Resource cleanup and garbage collection

## Testing Strategy

### Unit Testing
- Core business logic validation
- Data model testing
- Utility function testing
- Mock external service dependencies

### Integration Testing
- WhatsApp API integration
- Outlook integration (platform-specific)
- CSV processing with real files
- Configuration management

### UI Testing
- Widget functionality
- User workflow testing
- Accessibility compliance
- Cross-platform UI consistency

## Deployment Architecture

### Build Process
1. **Development**: Local development with virtual environment
2. **Testing**: Automated testing on CI/CD pipeline
3. **Packaging**: PyInstaller for executable creation
4. **Distribution**: Platform-specific installers

### Platform-Specific Considerations

#### Windows
- COM object integration for Outlook
- Windows-specific file paths and registry
- Code signing for executable trust

#### macOS
- AppleScript integration for Outlook
- macOS app bundle structure
- Notarization for security compliance
