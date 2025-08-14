# Message Logging and Analytics System

## Overview

The CSC-Reach application now includes a comprehensive message logging and analytics system that provides users with complete control and visibility over their messaging activity. This system tracks every message sent, provides detailed analytics, and enables data-driven insights for improving communication effectiveness.

## Key Features

### 1. Comprehensive Message Logging
- **Every Message Tracked**: All email and WhatsApp messages are logged with detailed metadata
- **Session Management**: Messages are grouped into sessions for bulk operations
- **Real-time Status Updates**: Track message status from pending to sent/failed
- **Error Tracking**: Detailed error messages and failure analysis
- **Content Preview**: First 100 characters of each message for quick identification

### 2. User Analytics Dashboard
- **Quick Statistics**: Messages sent, success rates, active sessions
- **Historical Analysis**: View messaging activity over customizable time periods
- **Channel Performance**: Compare success rates across email and WhatsApp
- **Template Effectiveness**: Analyze which templates perform best
- **Recipient Insights**: Track messaging frequency and response patterns

### 3. Data Export and Control
- **Multiple Export Formats**: JSON and CSV export options
- **Flexible Time Ranges**: Export data for any time period
- **Complete Data Portability**: Users own their data completely
- **Privacy Controls**: Data stored locally, never transmitted externally

### 4. Data Management
- **Automatic Cleanup**: Configurable retention policies
- **Storage Optimization**: Efficient SQLite database with indexing
- **Performance Monitoring**: Track database size and performance
- **Backup Support**: Easy backup and restore of messaging data

## System Architecture

### Core Components

1. **MessageLogger**: Central logging system with SQLite backend
2. **MessageAnalyticsDialog**: Comprehensive GUI for viewing logs and analytics
3. **LoggedEmailService**: Enhanced email service with integrated logging
4. **ApplicationManager**: Manages logger lifecycle and integration

### Data Models

- **MessageLogEntry**: Individual message log with full metadata
- **SessionSummary**: Aggregated statistics for bulk operations
- **AnalyticsReport**: Comprehensive analytics with insights and recommendations

## Usage Examples

### Basic Integration

```python
from src.multichannel_messaging.core.message_logger import MessageLogger
from src.multichannel_messaging.services.logged_email_service import LoggedEmailService

# Initialize logger
message_logger = MessageLogger(user_id="user123")

# Create enhanced email service
email_service = LoggedEmailService(message_logger)

# Send single email with logging
message_record = email_service.send_single_email(customer, template)
print(f"Message status: {message_record.status}")

# Send bulk emails with session tracking
message_records = email_service.send_bulk_emails(customers, template)
print(f"Sent {len([r for r in message_records if r.status == 'sent'])} messages")
```

### Analytics and Reporting

```python
# Get quick statistics
stats = message_logger.get_quick_stats()
print(f"Messages last 30 days: {stats['messages_last_30_days']}")
print(f"Success rate: {stats['success_rate_30_days']}%")

# Generate comprehensive analytics report
report = message_logger.generate_analytics_report(days=30)
print(f"Total messages: {report.total_messages_sent}")
print(f"Success rate: {report.overall_success_rate}%")

# Export data
json_data = message_logger.export_data("json", days=30)
with open("messaging_data.json", "w") as f:
    f.write(json_data)
```

### GUI Integration

```python
# Show analytics dialog (from main window)
def show_message_analytics(self):
    if self.message_logger:
        from .message_analytics_dialog import MessageAnalyticsDialog
        dialog = MessageAnalyticsDialog(self.message_logger, self)
        dialog.exec()
```

## Database Schema

### message_logs Table
- `id`: Unique log entry identifier
- `timestamp`: When the message was processed
- `user_id`: User identifier
- `session_id`: Session identifier for bulk operations
- `channel`: Communication channel (email, whatsapp)
- `template_id`: Template used
- `recipient_*`: Recipient information (email, name, phone, company)
- `message_status`: Current status (pending, sending, sent, failed, cancelled)
- `error_message`: Error details if failed
- `sent_at`: Timestamp when successfully sent
- `content_preview`: First 100 characters of message content

### session_summaries Table
- `session_id`: Unique session identifier
- `user_id`: User identifier
- `start_time`: Session start timestamp
- `end_time`: Session end timestamp
- `channel`: Channel used for session
- `template_used`: Template name
- `total_messages`: Total messages in session
- `successful_messages`: Successfully sent messages
- `failed_messages`: Failed messages
- `success_rate`: Calculated success percentage

### analytics_cache Table
- `report_id`: Unique report identifier
- `user_id`: User identifier
- `generated_at`: Report generation timestamp
- `date_range_start`: Analysis start date
- `date_range_end`: Analysis end date
- `report_data`: Cached report JSON

## Configuration Options

### Application Manager Integration
```python
# In config/default_config.yaml
user:
  id: "default_user"  # Unique user identifier

logging:
  message_logging_enabled: true
  retention_days: 90
  analytics_cache_hours: 1

monitoring:
  interval_ms: 30000  # Health monitoring interval
```

### Message Logger Settings
```python
# Initialize with custom settings
message_logger = MessageLogger(
    db_path="custom/path/messages.db",
    user_id="custom_user_id"
)

# Configure retention
message_logger.delete_old_data(days=60)  # Keep 60 days of data
```

## Privacy and Security

### Data Protection
- **Local Storage Only**: All data stored locally in SQLite database
- **No External Transmission**: Message content never sent to external servers
- **User Ownership**: Users have complete control over their data
- **Secure Deletion**: Proper data cleanup with configurable retention

### Compliance Features
- **Data Export**: Full data portability for compliance requirements
- **Audit Trail**: Complete history of all messaging activity
- **Retention Policies**: Configurable data retention periods
- **Access Control**: User-specific data isolation

## Performance Considerations

### Database Optimization
- **Indexed Queries**: Optimized indexes for common query patterns
- **Efficient Storage**: Compressed JSON for metadata storage
- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Optimized bulk insert/update operations

### Memory Management
- **Lazy Loading**: Analytics reports generated on-demand
- **Caching**: Intelligent caching of frequently accessed data
- **Cleanup**: Automatic cleanup of old cache entries
- **Resource Monitoring**: Built-in performance monitoring

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
   - Ensure proper connection cleanup
   - Check for long-running transactions
   - Verify file permissions

2. **Performance Issues**
   - Run database cleanup regularly
   - Check database size and indexes
   - Monitor memory usage

3. **Missing Analytics**
   - Verify message logger initialization
   - Check database connectivity
   - Ensure proper session management

### Debug Commands

```python
# Check database health
stats = message_logger.get_quick_stats()
print(f"Database status: {stats}")

# Verify recent activity
recent = message_logger.get_message_history(days=1)
print(f"Recent messages: {len(recent)}")

# Test database connection
try:
    message_logger._init_database()
    print("Database connection OK")
except Exception as e:
    print(f"Database error: {e}")
```

## Future Enhancements

### Planned Features
- **Advanced Analytics**: Machine learning insights and recommendations
- **Real-time Dashboards**: Live monitoring of messaging activity
- **Integration APIs**: REST API for external analytics tools
- **Advanced Filtering**: Complex query builder for data analysis
- **Automated Reports**: Scheduled analytics reports via email

### Extensibility
- **Plugin Architecture**: Support for custom analytics plugins
- **Custom Metrics**: User-defined KPIs and measurements
- **External Integrations**: Connect to business intelligence tools
- **Advanced Visualizations**: Interactive charts and graphs

## Support and Documentation

For additional support or questions about the message logging system:

1. Check the application logs in `logs/app.log`
2. Review the database schema documentation
3. Consult the API documentation for programmatic access
4. Contact support with specific error messages and log files

The message logging system is designed to provide complete transparency and control over your messaging activities while maintaining the highest standards of privacy and security.