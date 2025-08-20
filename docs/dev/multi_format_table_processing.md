# Multi-Format Table Processing

The CSC-Reach application now supports importing customer data from multiple table formats, not just CSV files. This document describes the enhanced table processing capabilities.

## Supported Formats

### Text-Based Formats
- **CSV** (Comma-Separated Values) - `.csv`, `.txt`
- **TSV** (Tab-Separated Values) - `.tsv`
- **Pipe-delimited** - `.txt` with `|` delimiter
- **Semicolon-delimited** - `.txt` with `;` delimiter

### Spreadsheet Formats
- **Excel XLSX** - `.xlsx` (requires `openpyxl`)
- **Excel XLS** - `.xls` (requires `xlrd`)

### JSON Formats
- **JSON** - `.json` (array of objects)
- **JSONL/NDJSON** - `.jsonl`, `.ndjson` (JSON Lines format)

## Key Features

### Automatic Format Detection
The system automatically detects file formats based on:
1. File extension analysis
2. Content pattern recognition
3. Delimiter frequency analysis
4. JSON structure validation

### Robust Processing
- **Encoding Detection**: Automatic detection of file encoding with confidence scoring
- **Intelligent Parsing**: Format-specific parsing optimized for each file type
- **Column Mapping**: Automatic mapping of columns to required fields (name, company, phone, email)
- **Data Validation**: Comprehensive validation with detailed error reporting
- **Memory Efficiency**: Streaming support for large files

### Error Handling
- Graceful handling of malformed files
- Detailed error reporting with suggestions
- Fallback mechanisms for ambiguous formats
- Validation warnings for data quality issues

## Usage Examples

### Basic Usage

```python
from multichannel_messaging.core.csv_processor import AdvancedTableProcessor

# Create processor
processor = AdvancedTableProcessor()

# Analyze any supported file format
structure = processor.analyze_file_structure(file_path)
print(f"Format: {structure.file_format.value}")
print(f"Columns: {structure.headers}")
print(f"Rows: {structure.total_rows}")

# Load customers from any format
customers, report = processor.load_customers_advanced(file_path)
print(f"Loaded {len(customers)} customers")
print(f"Success rate: {report.success_rate:.1f}%")
```

### Format-Specific Features

#### Excel Files
```python
# Specify sheet name for Excel files
structure = processor.analyze_file_structure(excel_file, sheet_name="Customers")
customers, report = processor.load_customers_advanced(excel_file, sheet_name="Customers")

# List available sheets
print(f"Available sheets: {structure.sheet_names}")
```

#### JSON Files
```python
# JSON array format
[
  {"name": "John Doe", "company": "Example Corp", "phone": "+1-555-0123", "email": "john@example.com"},
  {"name": "Jane Smith", "company": "Sample Inc", "phone": "+1-555-0456", "email": "jane@sample.com"}
]

# JSONL format (one JSON object per line)
{"name": "John Doe", "company": "Example Corp", "phone": "+1-555-0123", "email": "john@example.com"}
{"name": "Jane Smith", "company": "Sample Inc", "phone": "+1-555-0456", "email": "jane@sample.com"}
```

### Streaming Large Files
```python
# Stream processing for memory efficiency
for chunk in processor.stream_table_rows(file_path, chunk_size=1000):
    for row in chunk:
        # Process each row
        print(f"Processing: {row['name']}")
```

### Validation
```python
# Comprehensive validation
validation_result = processor.validate_table_format(file_path)

if validation_result['valid']:
    print("File is valid!")
    print(f"Format: {validation_result['analysis']['file_format']}")
    print(f"Required columns found: {validation_result['analysis']['required_columns_found']}")
else:
    print("Validation errors:")
    for error in validation_result['errors']:
        print(f"  - {error}")
```

## Architecture

### Class Structure

```
AdvancedTableProcessor
├── Format Detection
│   ├── detect_file_format()
│   └── _detect_format_by_content()
├── Structure Analysis
│   ├── analyze_file_structure()
│   ├── _analyze_excel_structure()
│   ├── _analyze_json_structure()
│   ├── _analyze_jsonl_structure()
│   └── _analyze_csv_like_structure()
├── Data Streaming
│   ├── stream_table_rows()
│   ├── _stream_excel_rows()
│   ├── _stream_json_rows()
│   ├── _stream_jsonl_rows()
│   └── _stream_csv_like_rows()
└── Validation & Loading
    ├── validate_table_comprehensive()
    ├── load_customers_advanced()
    ├── _load_customers_streaming()
    └── _load_customers_batch()
```

### Data Structures

#### FileFormat Enum
```python
class FileFormat(Enum):
    CSV = "csv"
    TSV = "tsv"
    EXCEL_XLSX = "xlsx"
    EXCEL_XLS = "xls"
    JSON = "json"
    JSONL = "jsonl"
    PIPE_DELIMITED = "pipe"
    SEMICOLON_DELIMITED = "semicolon"
    UNKNOWN = "unknown"
```

#### FileStructure
```python
@dataclass
class FileStructure:
    file_format: FileFormat
    encoding: Optional[EncodingResult] = None
    delimiter: Optional[DelimiterResult] = None
    headers: List[str] = field(default_factory=list)
    total_rows: int = 0
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)
    has_header: bool = True
    sheet_names: Optional[List[str]] = None  # For Excel files
    active_sheet: Optional[str] = None  # For Excel files
```

## Dependencies

### Required
- `pandas>=2.0.0` - Core data processing
- `chardet>=5.0.0` - Encoding detection

### Optional (for specific formats)
- `openpyxl>=3.1.0` - Excel XLSX support
- `xlrd>=2.0.0` - Excel XLS support

## Backward Compatibility

All existing CSV-specific methods remain available:
- `load_customers()` - Legacy customer loading
- `validate_csv_format()` - Legacy CSV validation
- `stream_csv_rows()` - Legacy CSV streaming
- `CSVProcessor` - Alias for `AdvancedTableProcessor`

## Performance Considerations

### Memory Usage
- **Streaming**: Use `stream_processing=True` for files > 5000 rows
- **Batch Processing**: Faster for smaller files
- **Format Impact**: JSON/Excel files require more memory than CSV

### Processing Speed
1. **CSV/TSV**: Fastest (native text processing)
2. **JSON/JSONL**: Fast (efficient JSON parsing)
3. **Excel**: Slower (requires pandas Excel engine)

### Recommendations
- Use CSV/TSV for best performance
- Enable streaming for large datasets
- Consider file size when choosing batch vs. streaming

## Error Handling

### Common Issues
1. **Missing Dependencies**: Clear error messages for missing libraries
2. **Malformed Files**: Graceful handling with detailed error reports
3. **Encoding Issues**: Automatic fallback with confidence scoring
4. **Column Mapping**: Intelligent suggestions for unmapped columns

### Error Recovery
- Multiple encoding detection strategies
- Flexible delimiter detection
- Partial data recovery for corrupted files
- Detailed validation reports with suggestions

## Testing

### Unit Tests
- Format detection accuracy
- Structure analysis correctness
- Streaming consistency
- Error handling robustness

### Integration Tests
- End-to-end processing workflows
- Cross-format consistency
- Performance benchmarks
- Memory usage validation

## Future Enhancements

### Planned Features
- **Google Sheets API** integration
- **Parquet** file support
- **Database** direct import
- **XML** table support
- **Custom delimiter** detection

### Performance Improvements
- **Parallel processing** for large files
- **Caching** for repeated operations
- **Compression** support
- **Incremental loading** for updates

## Migration Guide

### From CSV-Only to Multi-Format

#### Before (CSV only)
```python
processor = CSVProcessor()
customers, errors = processor.load_customers(csv_file)
```

#### After (Multi-format)
```python
processor = AdvancedTableProcessor()
customers, report = processor.load_customers_advanced(any_file)
```

### Updating Existing Code
1. Replace `CSVProcessor` with `AdvancedTableProcessor` (optional - alias exists)
2. Use `load_customers_advanced()` for enhanced features
3. Handle new file formats in file selection dialogs
4. Update validation logic to use `validate_table_format()`

The system maintains full backward compatibility, so existing code continues to work without changes.