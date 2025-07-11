# Channel Mapping System - Technical Documentation

## Overview

The channel mapping system handles the selection and routing of messages through different communication channels (Email, WhatsApp Business, WhatsApp Web) with full internationalization support.

## Architecture

### Channel Data Structure

The channel combo box stores data as `(display_text, channel_id)` pairs:

```python
channel_options = [
    (tr("email_only"), "email_only"),
    (tr("whatsapp_business_api"), "whatsapp_business"),
    (tr("whatsapp_web"), "whatsapp_web"),
    (tr("email_whatsapp_business"), "email_whatsapp_business"),
    (tr("email_whatsapp_web"), "email_whatsapp_web")
]
```

### Channel IDs

| Channel ID | Description | Functionality |
|------------|-------------|---------------|
| `email_only` | Email Only | Sends messages via Outlook email only |
| `whatsapp_business` | WhatsApp Business API | Uses WhatsApp Business API |
| `whatsapp_web` | WhatsApp Web | Uses WhatsApp Web automation |
| `email_whatsapp_business` | Email + WhatsApp Business | Dual channel via email and WhatsApp Business |
| `email_whatsapp_web` | Email + WhatsApp Web | Dual channel via email and WhatsApp Web |

## Internationalization Support

### Translation Keys

| Key | English | Portuguese | Spanish |
|-----|---------|------------|---------|
| `email_only` | Email Only | Apenas Email | Solo Email |
| `whatsapp_business_api` | WhatsApp Business API | WhatsApp Business API | WhatsApp Business API |
| `whatsapp_web` | WhatsApp Web | WhatsApp Web | WhatsApp Web |
| `email_whatsapp_business` | Email + WhatsApp Business | Email + WhatsApp Business | Email + WhatsApp Business |
| `email_whatsapp_web` | Email + WhatsApp Web | Email + WhatsApp Web | Email + WhatsApp Web |

### Language-Independent Operation

The system uses channel IDs internally, ensuring that:
- Channel selection works consistently across all languages
- No "Unknown channel" errors occur with translated text
- Channel routing logic is language-independent

## API Reference

### MainWindow Methods

#### `get_current_channel_id() -> str`

Returns the current channel ID from the combo box.

**Returns:**
- `str`: Channel ID (e.g., 'email_only', 'whatsapp_business')

**Example:**
```python
channel_id = self.get_current_channel_id()
if channel_id == "email_only":
    self.start_email_sending(customers)
```

#### `start_multi_channel_sending(customers: List[Customer], channel_id: str)`

Routes message sending based on channel ID.

**Parameters:**
- `customers`: List of customers to send messages to
- `channel_id`: Channel identifier for routing

**Channel Routing:**
```python
if channel_id == "email_only":
    self.start_email_sending(customers)
elif channel_id == "whatsapp_business":
    self.start_whatsapp_business_sending(customers)
elif channel_id == "whatsapp_web":
    self.start_whatsapp_web_sending(customers)
elif channel_id == "email_whatsapp_business":
    self.start_email_and_whatsapp_business_sending(customers)
elif channel_id == "email_whatsapp_web":
    self.start_email_and_whatsapp_web_sending(customers)
```

#### `_get_channel_description(channel_id: str) -> str`

Returns user-friendly description for confirmation dialogs.

**Parameters:**
- `channel_id`: Channel identifier

**Returns:**
- `str`: Human-readable channel description

**Mapping:**
```python
descriptions = {
    "email_only": "email",
    "whatsapp_business": "WhatsApp Business API",
    "whatsapp_web": "WhatsApp Web (manual sending required)",
    "email_whatsapp_business": "email and WhatsApp Business API",
    "email_whatsapp_web": "email and WhatsApp Web"
}
```

## Email Formatting System

### AppleScript Line Break Handling

The macOS Outlook service properly handles line breaks in email content:

```python
def _escape_for_applescript(self, text: str) -> str:
    """Escape text for AppleScript, preserving line breaks."""
    # Normalize line endings
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Escape special characters
    escaped = normalized.replace('\\', '\\\\')
    escaped = escaped.replace('"', '\\"')
    
    # Convert \n to \r for AppleScript
    escaped = escaped.replace('\n', '\\r')
    
    return escaped
```

### Line Break Preservation

Email content maintains proper formatting:

**Input:**
```
Dear {name},

Thank you for your interest.

Best regards,
The Team
```

**Output (preserved formatting):**
```
Dear Lucas Alves,

Thank you for your interest.

Best regards,
The Team
```

## Error Handling

### Channel Validation

The system validates channel availability before sending:

```python
# Email channel validation
if channel_id in ["email_only", "email_whatsapp_business", "email_whatsapp_web"]:
    if not self.email_service:
        QMessageBox.warning(self, "Email Service Error", "Email service is not available.")
        return

# WhatsApp Business validation
if channel_id in ["whatsapp_business", "email_whatsapp_business"]:
    if not self.whatsapp_service.is_configured():
        QMessageBox.warning(self, "WhatsApp Business API Not Configured", 
                          "Please configure WhatsApp Business API settings first.")
        return
```

### Fallback Behavior

- If no channel is selected, defaults to `"email_only"`
- Unknown channel IDs trigger warning dialog
- Graceful degradation for missing services

## Testing

### Unit Tests

Located in `tests/unit/test_email_channel_fixes.py`:

- Channel translation validation
- AppleScript escaping verification
- Email formatting preservation
- Channel ID consistency checks

### Test Coverage

- ✅ All language translations
- ✅ Channel ID mapping
- ✅ AppleScript line break handling
- ✅ Email content formatting
- ✅ Error handling scenarios

## Migration Notes

### Breaking Changes

The channel mapping system changed from using translated text to channel IDs:

**Before (❌ Problematic):**
```python
channel = self.channel_combo.currentText()  # "Apenas Email"
if channel == "Email Only":  # Fails with Portuguese!
    self.start_email_sending(customers)
```

**After (✅ Fixed):**
```python
channel_id = self.get_current_channel_id()  # "email_only"
if channel_id == "email_only":  # Works in all languages!
    self.start_email_sending(customers)
```

### Backward Compatibility

Legacy methods still work:
- `send_emails()` - Sets channel to email_only and calls `send_messages()`
- `preview_email()` - Temporarily sets channel to email_only for preview

## Best Practices

### Adding New Channels

1. **Add channel ID** to the channel options list
2. **Add translation keys** to all language files (en/pt/es)
3. **Update channel routing** in `start_multi_channel_sending()`
4. **Add channel description** to `_get_channel_description()`
5. **Add validation logic** if needed
6. **Write unit tests** for the new channel

### Internationalization

- Always use `tr()` for display text
- Use consistent channel IDs internally
- Test with all supported languages
- Avoid hardcoded English text in logic

### Error Handling

- Validate channel availability before operations
- Provide clear error messages with solutions
- Use graceful fallbacks for missing services
- Log channel operations for debugging

## Troubleshooting

### Common Issues

**"Unknown channel" error:**
- Ensure channel ID exists in routing logic
- Check that combo box data is properly set
- Verify translation keys are present

**Email formatting issues:**
- Check AppleScript escaping logic
- Verify line break conversion (\n to \r)
- Test with various content types

**Translation problems:**
- Ensure all language files have required keys
- Check i18n manager initialization
- Verify language switching works correctly

### Debug Information

Enable debug logging to see channel operations:
```python
logger.debug(f"Current channel ID: {channel_id}")
logger.debug(f"AppleScript escaping: {len(text)} chars -> {len(escaped)} chars")
```
