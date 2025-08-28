# CSC-Reach - Data System Documentation

## Overview

CSC-Reach utilizes a hybrid data architecture combining SQLite for persistent storage with multi-format file processing capabilities. The system handles customer data import, template management, message logging, and analytics with robust data validation and security measures.

## Database Schema

### SQLite Tables

#### customers
**Purpose**: Store customer contact information and preferences
- `id` (INTEGER, PK) - Unique customer identifier
- `name` (TEXT, NOT NULL) - Customer full name
- `company` (TEXT, NOT NULL) - Company name
- `email` (TEXT, NOT NULL) - Email address
- `phone` (TEXT, NOT NULL) - Phone number
- `whatsapp_opt_in` (BOOLEAN, DEFAULT TRUE) - WhatsApp consent
- `preferred_channel` (TEXT, DEFAULT 'both') - Communication preference
- `created_at` (DATETIME, NOT NULL) - Record creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last modification timestamp

**Indexes**: 
- `idx_customers_email` on `email`
- `idx_customers_company` on `company`

#### templates
**Purpose**: Store message templates with metadata
- `id` (TEXT, PK) - UUID template identifier
- `name` (TEXT, NOT NULL, UNIQUE) - Template display name
- `category` (TEXT, NOT NULL) - Template category (Welcome, Follow-up, etc.)
- `subject` (TEXT, NOT NULL) - Email subject line
- `content` (TEXT, NOT NULL) - Message content with variables
- `channel` (TEXT, NOT NULL) - Target channel (email, whatsapp, both)
- `variables` (TEXT) - JSON array of available variables
- `created_at` (DATETIME, NOT NULL) - Creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last modification timestamp
- `usage_count` (INTEGER, DEFAULT 0) - Usage statistics

**Constraints**:
- `CHECK (category IN ('Welcome', 'Follow-up', 'Promotional', 'Support', 'General'))`
- `CHECK (channel IN ('email', 'whatsapp', 'both'))`

#### campaigns
**Purpose**: Track bulk messaging campaigns
- `id` (TEXT, PK) - UUID campaign identifier
- `name` (TEXT, NOT NULL) - Campaign name
- `template_id` (TEXT, FK) - Reference to templates table
- `status` (TEXT, NOT NULL) - Campaign status
- `total_recipients` (INTEGER, NOT NULL) - Total target recipients
- `sent_count` (INTEGER, DEFAULT 0) - Successfully sent messages
- `failed_count` (INTEGER, DEFAULT 0) - Failed message attempts
- `created_at` (DATETIME, NOT NULL) - Campaign start time
- `completed_at` (DATETIME) - Campaign completion time

**Foreign Keys**:
- `template_id` REFERENCES `templates(id)` ON DELETE CASCADE

#### messages
**Purpose**: Log individual message sending attempts
- `id` (TEXT, PK) - UUID message identifier
- `campaign_id` (TEXT, FK) - Reference to campaigns table
- `customer_id` (INTEGER, FK) - Reference to customers table
- `template_id` (TEXT, FK) - Reference to templates table
- `channel` (TEXT, NOT NULL) - Delivery channel used
- `status` (TEXT, NOT NULL) - Message status
- `subject` (TEXT) - Actual subject sent
- `content` (TEXT) - Actual content sent (truncated for privacy)
- `error_message` (TEXT) - Error details if failed
- `sent_at` (DATETIME) - Sending timestamp
- `delivered_at` (DATETIME) - Delivery confirmation timestamp

**Foreign Keys**:
- `campaign_id` REFERENCES `campaigns(id)` ON DELETE CASCADE
- `customer_id` REFERENCES `customers(id)` ON DELETE CASCADE
- `template_id` REFERENCES `templates(id)` ON DELETE SET NULL

#### message_analytics
**Purpose**: Store campaign performance metrics
- `id` (INTEGER, PK) - Auto-increment identifier
- `campaign_id` (TEXT, FK) - Reference to campaigns table
- `metric_name` (TEXT, NOT NULL) - Metric identifier
- `metric_value` (REAL, NOT NULL) - Metric value
- `tags` (TEXT) - JSON object with additional metadata
- `recorded_at` (DATETIME, NOT NULL) - Metric recording time

#### configuration
**Purpose**: Store application configuration settings
- `key` (TEXT, PK) - Configuration key
- `value` (TEXT, NOT NULL) - Configuration value
- `data_type` (TEXT, NOT NULL) - Value data type
- `updated_at` (DATETIME, NOT NULL) - Last update timestamp

## Multi-Format Data Processing

### Supported Formats

#### Text-Based Formats
- **CSV** (Comma-Separated Values) - `.csv`, `.txt`
  - Automatic delimiter detection (comma, semicolon, pipe, tab)
  - Encoding detection (UTF-8, Latin-1, Windows-1252)
  - Quote character handling
- **TSV** (Tab-Separated Values) - `.tsv`
  - Tab delimiter with escape sequence support
- **Delimited Files** - `.txt`
  - Custom delimiter detection
  - Header row identification

#### Spreadsheet Formats
- **Excel XLSX** - `.xlsx` (modern Excel format)
  - Multiple worksheet support
  - Cell formatting preservation
  - Formula evaluation
- **Excel XLS** - `.xls` (legacy Excel format)
  - Backward compatibility
  - Limited to first worksheet

#### JSON Formats
- **JSON** - `.json` (array of objects)
  - Nested object flattening
  - Array handling for multiple values
- **JSONL/NDJSON** - `.jsonl`, `.ndjson` (JSON Lines format)
  - Streaming processing for large files
  - Memory-efficient parsing

### Processing Pipeline

#### 1. Format Detection
```python
def detect_format(file_path: str) -> str:
    # File extension analysis
    # Content pattern recognition
    # Delimiter frequency analysis
    # JSON structure validation
```

#### 2. Encoding Detection
- Automatic encoding detection using `chardet`
- Fallback encoding hierarchy: UTF-8 → Latin-1 → Windows-1252
- BOM (Byte Order Mark) handling

#### 3. Column Mapping
- Automatic mapping to required fields (name, company, email, phone)
- Fuzzy matching for similar column names
- User-configurable mapping overrides
- Validation of mapped data types

#### 4. Data Validation
- Email format validation (RFC 5322 compliance)
- Phone number format validation
- Required field presence checking
- Duplicate detection and handling
- Data quality scoring

## Data Flow Architecture

### Import Process
1. **File Selection** → User selects data file
2. **Format Detection** → Automatic format identification
3. **Parsing** → File content extraction
4. **Column Mapping** → Field mapping to schema
5. **Validation** → Data quality checks
6. **Storage** → Import to customers table

### Template Processing
1. **Template Selection** → User chooses message template
2. **Variable Extraction** → Identify template variables
3. **Data Binding** → Map customer data to variables
4. **Content Generation** → Personalized message creation
5. **Queue Management** → Batch processing preparation

### Message Delivery
1. **Channel Selection** → Email/WhatsApp routing
2. **Service Integration** → Platform-specific API calls
3. **Delivery Tracking** → Status monitoring
4. **Error Handling** → Retry logic and failure logging
5. **Analytics Collection** → Performance metrics

## Performance Optimizations

### Database Optimizations
- **Indexes**: Strategic indexing on frequently queried columns
- **Connection Pooling**: Reuse database connections
- **Batch Operations**: Bulk inserts for large datasets
- **Query Optimization**: Prepared statements and query planning

### Memory Management
- **Streaming Processing**: Large files processed in chunks
- **Lazy Loading**: Data loaded on-demand
- **Cache Management**: LRU cache for frequently accessed data
- **Resource Cleanup**: Automatic cleanup of temporary resources

### I/O Optimizations
- **Asynchronous Processing**: Non-blocking file operations
- **Compression**: Temporary file compression
- **Buffer Management**: Optimal buffer sizes for different file types

## Security and Privacy

### Data Protection
- **Encryption at Rest**: SQLite database encryption using SQLCipher
- **Secure Deletion**: Cryptographic erasure of sensitive data
- **Access Control**: File system permissions and user isolation
- **Audit Logging**: Comprehensive access and modification logs

### Privacy Compliance
- **Data Minimization**: Only necessary data fields stored
- **Retention Policies**: Automatic cleanup of old campaign data
- **Anonymization**: Personal data anonymization for analytics
- **Consent Management**: WhatsApp opt-in tracking

### Input Validation
- **SQL Injection Prevention**: Parameterized queries only
- **File Type Validation**: Strict file type checking
- **Size Limits**: Maximum file size enforcement
- **Content Scanning**: Malicious content detection

## Backup and Recovery

### Backup Strategy
- **Automatic Backups**: Daily SQLite database backups
- **Template Versioning**: Version control for template changes
- **Configuration Backup**: Settings and preferences backup
- **Export Functionality**: Data export in multiple formats

### Recovery Procedures
- **Database Recovery**: Point-in-time recovery from backups
- **Template Recovery**: Rollback to previous template versions
- **Data Validation**: Integrity checks after recovery
- **Migration Support**: Schema migration for version updates

## ETL Processes

### Extract Phase
- Multi-format file reading
- Encoding detection and conversion
- Error handling and logging
- Progress tracking for large files

### Transform Phase
- Column mapping and normalization
- Data type conversion
- Validation and cleansing
- Duplicate detection and merging

### Load Phase
- Batch insertion to database
- Referential integrity maintenance
- Index rebuilding
- Statistics update

## Monitoring and Analytics

### Performance Metrics
- **Processing Speed**: Records per second
- **Memory Usage**: Peak and average memory consumption
- **Error Rates**: Processing failure percentages
- **Response Times**: Database query performance

### Business Metrics
- **Campaign Success Rates**: Delivery success percentages
- **Template Usage**: Most popular templates
- **Channel Performance**: Email vs WhatsApp effectiveness
- **Customer Engagement**: Response and interaction rates

## Glossary

### Business Terms
- **Campaign**: A bulk messaging operation targeting multiple customers
- **Template**: A reusable message format with variable placeholders
- **Channel**: Communication method (email or WhatsApp)
- **Variable**: Dynamic content placeholder in templates (e.g., {name})
- **Opt-in**: Customer consent for WhatsApp messaging

### Technical Terms
- **ETL**: Extract, Transform, Load data processing
- **JSONL**: JSON Lines format with one JSON object per line
- **SQLite**: Embedded relational database engine
- **UUID**: Universally Unique Identifier
- **RFC 5322**: Internet Message Format standard for email

## Schema Versioning

### Current Version: 1.2.0

### Migration History
- **1.0.0**: Initial schema with basic tables
- **1.1.0**: Added message_analytics table
- **1.2.0**: Added configuration table and indexes

### Migration Process
1. **Backup**: Create full database backup
2. **Schema Update**: Apply DDL changes
3. **Data Migration**: Transform existing data if needed
4. **Validation**: Verify data integrity
5. **Rollback Plan**: Prepared rollback procedures

### Future Migrations
- **1.3.0**: Planned addition of user management tables
- **1.4.0**: Enhanced analytics with time-series data
- **2.0.0**: Potential migration to PostgreSQL for enterprise features
