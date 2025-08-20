"""
Advanced Table file processing for Multi-Channel Bulk Messaging System.
Enhanced with robust encoding detection, intelligent parsing, and comprehensive validation.
Supports CSV, Excel, Google Sheets, TSV, and other tabular formats.
"""

import csv
import pandas as pd
import re
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import codecs
import json

try:
    import chardet
except ImportError:
    chardet = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None

from .models import Customer
from .column_mapper import IntelligentColumnMapper, MappingResult, ColumnMapping
from .data_validator import AdvancedDataValidator, ValidationResult
from ..utils.exceptions import CSVProcessingError, ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileFormat(Enum):
    """Supported file formats."""
    CSV = "csv"
    TSV = "tsv"
    EXCEL_XLSX = "xlsx"
    EXCEL_XLS = "xls"
    JSON = "json"
    JSONL = "jsonl"
    PIPE_DELIMITED = "pipe"
    SEMICOLON_DELIMITED = "semicolon"
    UNKNOWN = "unknown"


class EncodingConfidence(Enum):
    """Encoding detection confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FALLBACK = "fallback"


@dataclass
class EncodingResult:
    """Result of encoding detection."""
    encoding: str
    confidence: EncodingConfidence
    confidence_score: float = 0.0
    detected_by: str = "unknown"
    
    
@dataclass
class DelimiterResult:
    """Result of delimiter detection."""
    delimiter: str
    confidence: float
    quote_char: str = '"'
    escape_char: Optional[str] = None
    detected_by: str = "sniffer"


@dataclass
class FileStructure:
    """Table file structure information."""
    file_format: FileFormat
    encoding: Optional[EncodingResult] = None
    delimiter: Optional[DelimiterResult] = None
    headers: List[str] = field(default_factory=list)
    total_rows: int = 0
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)
    has_header: bool = True
    quote_style: int = csv.QUOTE_MINIMAL
    line_terminator: str = '\n'
    sheet_names: Optional[List[str]] = None  # For Excel files
    active_sheet: Optional[str] = None  # For Excel files


# Backward compatibility alias
CSVStructure = FileStructure


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    row_number: int
    column: str
    value: Any
    issue_type: str
    message: str
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None


@dataclass
class TableValidationReport:
    """Comprehensive table validation report."""
    total_rows: int
    valid_rows: int
    file_format: FileFormat
    issues: List[ValidationIssue] = field(default_factory=list)
    encoding_issues: List[str] = field(default_factory=list)
    structure_issues: List[str] = field(default_factory=list)
    format_issues: List[str] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == "error"])
    
    @property
    def warning_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == "warning"])
    
    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return (self.valid_rows / self.total_rows) * 100


# Backward compatibility alias
CSVValidationReport = TableValidationReport


class AdvancedTableProcessor:
    """Advanced table file processor supporting multiple formats with enhanced parsing, validation, and error handling."""
    
    # Enhanced column mappings with pattern recognition
    COLUMN_MAPPINGS = {
        'name': {
            'exact': ['name', 'customer_name', 'full_name', 'client_name', 'nome', 'nombre', 'nom'],
            'patterns': [r'.*name.*', r'.*cliente.*', r'.*customer.*'],
            'weight': 1.0
        },
        'company': {
            'exact': ['company', 'company_name', 'organization', 'org', 'business', 'empresa', 'compañía', 'société'],
            'patterns': [r'.*company.*', r'.*organization.*', r'.*business.*', r'.*corp.*', r'.*empresa.*'],
            'weight': 1.0
        },
        'phone': {
            'exact': ['phone', 'telephone', 'mobile', 'cell', 'telefone', 'teléfono', 'téléphone'],
            'patterns': [r'.*phone.*', r'.*tel.*', r'.*mobile.*', r'.*cell.*'],
            'weight': 1.0
        },
        'email': {
            'exact': ['email', 'email_address', 'e-mail', 'mail', 'correo', 'courriel'],
            'patterns': [r'.*email.*', r'.*mail.*', r'.*@.*'],
            'weight': 1.0
        }
    }
    
    # Supported encodings in order of preference
    SUPPORTED_ENCODINGS = [
        'utf-8', 'utf-8-sig',  # UTF-8 with and without BOM
        'cp1252', 'windows-1252',  # Windows Western European
        'iso-8859-1', 'latin-1',  # Latin-1
        'iso-8859-15', 'latin-9',  # Latin-9 (with Euro symbol)
        'cp850',  # DOS Western European
        'ascii'  # ASCII fallback
    ]
    
    # Common delimiters to test
    COMMON_DELIMITERS = [',', ';', '\t', '|', ':']
    
    # Supported file extensions and their formats
    FORMAT_EXTENSIONS = {
        '.csv': FileFormat.CSV,
        '.tsv': FileFormat.TSV,
        '.txt': FileFormat.CSV,  # Assume CSV for .txt files
        '.xlsx': FileFormat.EXCEL_XLSX,
        '.xls': FileFormat.EXCEL_XLS,
        '.json': FileFormat.JSON,
        '.jsonl': FileFormat.JSONL,
        '.ndjson': FileFormat.JSONL,
    }

    def __init__(self, enable_domain_checking: bool = True):
        """Initialize advanced table processor."""
        self.last_structure: Optional[FileStructure] = None
        self.validation_cache: Dict[str, TableValidationReport] = {}
        self._encoding_cache: Dict[str, EncodingResult] = {}
        self.column_mapper = IntelligentColumnMapper()
        self.data_validator = AdvancedDataValidator(enable_domain_checking=enable_domain_checking)
    
    def detect_file_format(self, file_path: Path) -> FileFormat:
        """
        Detect file format based on extension and content analysis.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected file format
        """
        try:
            # First, try extension-based detection
            extension = file_path.suffix.lower()
            if extension in self.FORMAT_EXTENSIONS:
                detected_format = self.FORMAT_EXTENSIONS[extension]
                logger.debug(f"Format detected by extension: {detected_format.value}")
                
                # For ambiguous extensions, do content analysis
                if extension in ['.txt', '.csv']:
                    content_format = self._detect_format_by_content(file_path)
                    if content_format != FileFormat.UNKNOWN:
                        logger.debug(f"Format refined by content analysis: {content_format.value}")
                        return content_format
                
                return detected_format
            
            # If extension is unknown, analyze content
            content_format = self._detect_format_by_content(file_path)
            if content_format != FileFormat.UNKNOWN:
                logger.debug(f"Format detected by content analysis: {content_format.value}")
                return content_format
            
            logger.warning(f"Could not detect format for {file_path}, defaulting to CSV")
            return FileFormat.CSV
            
        except Exception as e:
            logger.error(f"Format detection failed: {e}")
            return FileFormat.UNKNOWN
    
    def _detect_format_by_content(self, file_path: Path) -> FileFormat:
        """Detect format by analyzing file content."""
        try:
            # Read first few bytes to analyze
            with open(file_path, 'rb') as f:
                first_bytes = f.read(1024)
            
            # Try to decode as text
            try:
                # Try UTF-8 first
                text_content = first_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Fall back to latin-1
                    text_content = first_bytes.decode('latin-1')
                except UnicodeDecodeError:
                    return FileFormat.UNKNOWN
            
            # Check for JSON format
            if text_content.strip().startswith(('{', '[')):
                try:
                    json.loads(text_content)
                    return FileFormat.JSON
                except json.JSONDecodeError:
                    # Might be JSONL
                    lines = text_content.strip().split('\n')
                    if len(lines) > 1:
                        try:
                            json.loads(lines[0])
                            return FileFormat.JSONL
                        except json.JSONDecodeError:
                            pass
            
            # Check for JSONL format (each line is JSON)
            lines = text_content.strip().split('\n')
            if len(lines) > 0:
                try:
                    json.loads(lines[0])
                    return FileFormat.JSONL
                except json.JSONDecodeError:
                    pass
            
            # Analyze delimiter patterns
            delimiter_counts = {
                ',': text_content.count(','),
                '\t': text_content.count('\t'),
                ';': text_content.count(';'),
                '|': text_content.count('|')
            }
            
            # Find most common delimiter
            max_delimiter = max(delimiter_counts.items(), key=lambda x: x[1])
            
            if max_delimiter[1] > 0:  # At least one delimiter found
                if max_delimiter[0] == '\t':
                    return FileFormat.TSV
                elif max_delimiter[0] == ';':
                    return FileFormat.SEMICOLON_DELIMITED
                elif max_delimiter[0] == '|':
                    return FileFormat.PIPE_DELIMITED
                else:  # comma or default
                    return FileFormat.CSV
            
            return FileFormat.UNKNOWN
            
        except Exception as e:
            logger.debug(f"Content-based format detection failed: {e}")
            return FileFormat.UNKNOWN
    
    def detect_encoding(self, file_path: Path, sample_size: int = 32768) -> EncodingResult:
        """
        Advanced encoding detection with multiple strategies and confidence scoring.
        
        Args:
            file_path: Path to CSV file
            sample_size: Number of bytes to read for detection
            
        Returns:
            EncodingResult with detected encoding and confidence
        """
        file_key = f"{file_path}:{file_path.stat().st_mtime}"
        if file_key in self._encoding_cache:
            return self._encoding_cache[file_key]
        
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
            
            if not raw_data:
                result = EncodingResult('utf-8', EncodingConfidence.FALLBACK, 0.0, 'empty_file')
                self._encoding_cache[file_key] = result
                return result
            
            # Strategy 1: Check for BOM (Byte Order Mark)
            bom_result = self._detect_bom(raw_data)
            if bom_result:
                logger.debug(f"BOM detected: {bom_result.encoding}")
                self._encoding_cache[file_key] = bom_result
                return bom_result
            
            # Strategy 2: Use chardet if available
            if chardet is not None:
                chardet_result = self._detect_with_chardet(raw_data)
                if chardet_result.confidence_score > 0.8:
                    logger.debug(f"High confidence chardet detection: {chardet_result.encoding}")
                    self._encoding_cache[file_key] = chardet_result
                    return chardet_result
            
            # Strategy 3: Systematic encoding testing
            systematic_result = self._detect_systematic(raw_data)
            if systematic_result.confidence != EncodingConfidence.FALLBACK:
                logger.debug(f"Systematic detection: {systematic_result.encoding}")
                self._encoding_cache[file_key] = systematic_result
                return systematic_result
            
            # Strategy 4: Content-based heuristics
            heuristic_result = self._detect_heuristic(raw_data)
            logger.debug(f"Heuristic detection: {heuristic_result.encoding}")
            self._encoding_cache[file_key] = heuristic_result
            return heuristic_result
            
        except Exception as e:
            logger.error(f"Encoding detection failed: {e}")
            result = EncodingResult('utf-8', EncodingConfidence.FALLBACK, 0.0, 'error_fallback')
            self._encoding_cache[file_key] = result
            return result
    
    def _detect_bom(self, raw_data: bytes) -> Optional[EncodingResult]:
        """Detect encoding from Byte Order Mark."""
        bom_signatures = [
            (codecs.BOM_UTF8, 'utf-8-sig'),
            (codecs.BOM_UTF16_LE, 'utf-16-le'),
            (codecs.BOM_UTF16_BE, 'utf-16-be'),
            (codecs.BOM_UTF32_LE, 'utf-32-le'),
            (codecs.BOM_UTF32_BE, 'utf-32-be'),
        ]
        
        for bom, encoding in bom_signatures:
            if raw_data.startswith(bom):
                return EncodingResult(encoding, EncodingConfidence.HIGH, 1.0, 'bom')
        
        return None
    
    def _detect_with_chardet(self, raw_data: bytes) -> EncodingResult:
        """Detect encoding using chardet library."""
        try:
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0.0)
            
            # Map confidence score to our confidence levels
            if confidence >= 0.9:
                conf_level = EncodingConfidence.HIGH
            elif confidence >= 0.7:
                conf_level = EncodingConfidence.MEDIUM
            elif confidence >= 0.5:
                conf_level = EncodingConfidence.LOW
            else:
                conf_level = EncodingConfidence.FALLBACK
            
            return EncodingResult(encoding, conf_level, confidence, 'chardet')
            
        except Exception as e:
            logger.warning(f"chardet detection failed: {e}")
            return EncodingResult('utf-8', EncodingConfidence.FALLBACK, 0.0, 'chardet_error')
    
    def _detect_systematic(self, raw_data: bytes) -> EncodingResult:
        """Systematically test encodings in order of preference."""
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                decoded = raw_data.decode(encoding)
                
                # Score the encoding based on content quality
                score = self._score_decoded_content(decoded, encoding)
                
                if score > 0.8:
                    return EncodingResult(encoding, EncodingConfidence.HIGH, score, 'systematic')
                elif score > 0.6:
                    return EncodingResult(encoding, EncodingConfidence.MEDIUM, score, 'systematic')
                elif score > 0.3:
                    return EncodingResult(encoding, EncodingConfidence.LOW, score, 'systematic')
                    
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return EncodingResult('utf-8', EncodingConfidence.FALLBACK, 0.0, 'systematic_fallback')
    
    def _detect_heuristic(self, raw_data: bytes) -> EncodingResult:
        """Use content heuristics to detect encoding."""
        # Try UTF-8 first as it's most common
        try:
            decoded = raw_data.decode('utf-8')
            score = self._score_decoded_content(decoded, 'utf-8')
            if score > 0.5:
                return EncodingResult('utf-8', EncodingConfidence.MEDIUM, score, 'heuristic')
        except UnicodeDecodeError:
            pass
        
        # Fall back to latin-1 which can decode any byte sequence
        try:
            decoded = raw_data.decode('latin-1')
            score = self._score_decoded_content(decoded, 'latin-1')
            return EncodingResult('latin-1', EncodingConfidence.LOW, score, 'heuristic_fallback')
        except UnicodeDecodeError:
            pass
        
        return EncodingResult('utf-8', EncodingConfidence.FALLBACK, 0.0, 'final_fallback')
    
    def _score_decoded_content(self, content: str, encoding: str) -> float:
        """Score decoded content quality for encoding detection."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Check for common CSV indicators
        if ',' in content or ';' in content or '\t' in content:
            score += 0.3
        
        # Check for reasonable character distribution
        printable_chars = sum(1 for c in content if c.isprintable() or c in '\n\r\t')
        if len(content) > 0:
            printable_ratio = printable_chars / len(content)
            score += printable_ratio * 0.4
        
        # Bonus for UTF-8
        if encoding == 'utf-8':
            score += 0.1
        
        # Check for email patterns (common in CSV files)
        if '@' in content and '.' in content:
            score += 0.1
        
        # Penalty for control characters (except common ones)
        control_chars = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
        if len(content) > 0:
            control_ratio = control_chars / len(content)
            score -= control_ratio * 0.3
        
        return max(0.0, min(1.0, score))
    
    def detect_delimiter(self, file_path: Path, encoding: str, sample_lines: int = 10) -> DelimiterResult:
        """
        Intelligent delimiter detection with confidence scoring.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding to use
            sample_lines: Number of lines to analyze
            
        Returns:
            DelimiterResult with detected delimiter and metadata
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read sample lines
                sample_lines_data = []
                for _ in range(sample_lines):
                    line = f.readline()
                    if not line:
                        break
                    sample_lines_data.append(line.rstrip('\n\r'))
                
                if not sample_lines_data:
                    return DelimiterResult(',', 0.0, detected_by='empty_file')
                
                sample = '\n'.join(sample_lines_data)
            
            # Strategy 1: Use CSV sniffer
            sniffer_result = self._detect_delimiter_sniffer(sample)
            if sniffer_result.confidence > 0.8:
                return sniffer_result
            
            # Strategy 2: Statistical analysis
            stats_result = self._detect_delimiter_statistical(sample_lines_data)
            if stats_result.confidence > sniffer_result.confidence:
                return stats_result
            
            # Strategy 3: Pattern-based detection
            pattern_result = self._detect_delimiter_pattern(sample)
            
            # Return the best result
            results = [sniffer_result, stats_result, pattern_result]
            best_result = max(results, key=lambda r: r.confidence)
            
            logger.debug(f"Delimiter detection: '{best_result.delimiter}' (confidence: {best_result.confidence:.2f})")
            return best_result
            
        except Exception as e:
            logger.warning(f"Delimiter detection failed: {e}")
            return DelimiterResult(',', 0.0, detected_by='error_fallback')
    
    def _detect_delimiter_sniffer(self, sample: str) -> DelimiterResult:
        """Use CSV sniffer for delimiter detection."""
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=',;\t|:')
            
            # Calculate confidence based on consistency
            lines = sample.split('\n')
            if len(lines) < 2:
                return DelimiterResult(dialect.delimiter, 0.1, dialect.quotechar, detected_by='sniffer')
            
            # Check consistency across lines
            delimiter_counts = []
            for line in lines[:5]:  # Check first 5 lines
                if line.strip():
                    delimiter_counts.append(line.count(dialect.delimiter))
            
            if delimiter_counts:
                avg_count = sum(delimiter_counts) / len(delimiter_counts)
                consistency = 1.0 - (max(delimiter_counts) - min(delimiter_counts)) / max(1, avg_count)
                confidence = min(0.9, consistency * 0.8 + 0.1)
            else:
                confidence = 0.1
            
            return DelimiterResult(
                dialect.delimiter, 
                confidence, 
                dialect.quotechar,
                getattr(dialect, 'escapechar', None),
                'sniffer'
            )
            
        except Exception as e:
            logger.debug(f"Sniffer detection failed: {e}")
            return DelimiterResult(',', 0.0, detected_by='sniffer_error')
    
    def _detect_delimiter_statistical(self, lines: List[str]) -> DelimiterResult:
        """Statistical delimiter detection based on frequency and consistency."""
        if not lines:
            return DelimiterResult(',', 0.0, detected_by='stats_empty')
        
        delimiter_stats = {}
        
        for delimiter in self.COMMON_DELIMITERS:
            counts = []
            for line in lines[:10]:  # Analyze first 10 lines
                if line.strip():
                    counts.append(line.count(delimiter))
            
            if not counts:
                continue
            
            # Calculate statistics
            avg_count = sum(counts) / len(counts)
            if avg_count == 0:
                continue
            
            # Consistency score (lower variance is better)
            variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
            consistency = 1.0 / (1.0 + variance)
            
            # Frequency score (more delimiters generally better for CSV)
            frequency_score = min(1.0, avg_count / 10.0)
            
            # Combined score
            score = (consistency * 0.7 + frequency_score * 0.3)
            delimiter_stats[delimiter] = {
                'score': score,
                'avg_count': avg_count,
                'consistency': consistency
            }
        
        if not delimiter_stats:
            return DelimiterResult(',', 0.0, detected_by='stats_no_delimiters')
        
        # Find best delimiter
        best_delimiter = max(delimiter_stats.keys(), key=lambda d: delimiter_stats[d]['score'])
        best_score = delimiter_stats[best_delimiter]['score']
        
        return DelimiterResult(best_delimiter, best_score, detected_by='statistical')
    
    def _detect_delimiter_pattern(self, sample: str) -> DelimiterResult:
        """Pattern-based delimiter detection using regex."""
        patterns = {
            ',': r'[^,\n]*,[^,\n]*',  # Comma-separated values
            ';': r'[^;\n]*;[^;\n]*',  # Semicolon-separated
            '\t': r'[^\t\n]*\t[^\t\n]*',  # Tab-separated
            '|': r'[^|\n]*\|[^|\n]*',  # Pipe-separated
        }
        
        scores = {}
        for delimiter, pattern in patterns.items():
            matches = re.findall(pattern, sample)
            if matches:
                # Score based on match frequency and line coverage
                lines = sample.split('\n')
                non_empty_lines = [line for line in lines if line.strip()]
                if non_empty_lines:
                    coverage = len(matches) / len(non_empty_lines)
                    scores[delimiter] = min(0.8, coverage)
        
        if not scores:
            return DelimiterResult(',', 0.0, detected_by='pattern_no_matches')
        
        best_delimiter = max(scores.keys(), key=lambda d: scores[d])
        return DelimiterResult(best_delimiter, scores[best_delimiter], detected_by='pattern')
    
    def analyze_file_structure(self, file_path: Path, sheet_name: Optional[str] = None) -> FileStructure:
        """
        Comprehensive table file structure analysis supporting multiple formats.
        
        Args:
            file_path: Path to table file
            sheet_name: Sheet name for Excel files (optional)
            
        Returns:
            FileStructure with complete file analysis
        """
        try:
            # Step 1: Detect file format
            file_format = self.detect_file_format(file_path)
            logger.debug(f"File format detected: {file_format.value}")
            
            # Step 2: Analyze based on format
            if file_format in [FileFormat.EXCEL_XLSX, FileFormat.EXCEL_XLS]:
                structure = self._analyze_excel_structure(file_path, file_format, sheet_name)
            elif file_format == FileFormat.JSON:
                structure = self._analyze_json_structure(file_path)
            elif file_format == FileFormat.JSONL:
                structure = self._analyze_jsonl_structure(file_path)
            else:
                # Handle CSV-like formats (CSV, TSV, pipe-delimited, etc.)
                structure = self._analyze_csv_like_structure(file_path, file_format)
            
            self.last_structure = structure
            logger.info(f"Analyzed {file_format.value}: {len(structure.headers)} columns, {structure.total_rows} rows")
            
            return structure
            
        except Exception as e:
            logger.error(f"File structure analysis failed: {e}")
            raise CSVProcessingError(f"Failed to analyze table file structure: {e}")
    
    def _analyze_excel_structure(self, file_path: Path, file_format: FileFormat, sheet_name: Optional[str] = None) -> FileStructure:
        """Analyze Excel file structure."""
        try:
            # Check if required libraries are available
            if file_format == FileFormat.EXCEL_XLSX and openpyxl is None:
                raise CSVProcessingError("openpyxl library is required for .xlsx files. Install with: pip install openpyxl")
            if file_format == FileFormat.EXCEL_XLS and xlrd is None:
                raise CSVProcessingError("xlrd library is required for .xls files. Install with: pip install xlrd")
            
            # Read Excel file with pandas
            if file_format == FileFormat.EXCEL_XLSX:
                # Get sheet names first
                excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            else:
                excel_file = pd.ExcelFile(file_path, engine='xlrd')
            
            sheet_names = excel_file.sheet_names
            active_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0]
            
            # Read the specified sheet
            df = pd.read_excel(file_path, sheet_name=active_sheet, engine='openpyxl' if file_format == FileFormat.EXCEL_XLSX else 'xlrd')
            
            # Clean up the dataframe
            df = df.dropna(how='all')  # Remove completely empty rows
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unnamed columns
            
            # Extract structure information
            headers = [str(col) for col in df.columns.tolist()]
            total_rows = len(df)
            
            # Get sample data
            sample_size = min(5, total_rows)
            sample_rows = []
            for i in range(sample_size):
                row_dict = {}
                for col in headers:
                    value = df.iloc[i][col]
                    if pd.isna(value):
                        row_dict[col] = ""
                    else:
                        row_dict[col] = str(value)
                sample_rows.append(row_dict)
            
            return FileStructure(
                file_format=file_format,
                headers=headers,
                total_rows=total_rows,
                sample_rows=sample_rows,
                has_header=True,
                sheet_names=sheet_names,
                active_sheet=active_sheet
            )
            
        except Exception as e:
            logger.error(f"Excel structure analysis failed: {e}")
            raise CSVProcessingError(f"Failed to analyze Excel file: {e}")
    
    def _analyze_json_structure(self, file_path: Path) -> FileStructure:
        """Analyze JSON file structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of objects
                if not data:
                    return FileStructure(file_format=FileFormat.JSON, headers=[], total_rows=0, sample_rows=[])
                
                # Extract headers from first object
                first_item = data[0]
                if isinstance(first_item, dict):
                    headers = list(first_item.keys())
                    total_rows = len(data)
                    
                    # Get sample data
                    sample_size = min(5, total_rows)
                    sample_rows = []
                    for i in range(sample_size):
                        item = data[i]
                        if isinstance(item, dict):
                            row_dict = {key: str(item.get(key, "")) for key in headers}
                            sample_rows.append(row_dict)
                    
                    return FileStructure(
                        file_format=FileFormat.JSON,
                        headers=headers,
                        total_rows=total_rows,
                        sample_rows=sample_rows,
                        has_header=True
                    )
            
            elif isinstance(data, dict):
                # Single object - treat as one row
                headers = list(data.keys())
                sample_rows = [{key: str(data.get(key, "")) for key in headers}]
                
                return FileStructure(
                    file_format=FileFormat.JSON,
                    headers=headers,
                    total_rows=1,
                    sample_rows=sample_rows,
                    has_header=True
                )
            
            raise CSVProcessingError("Unsupported JSON structure - expected array of objects or single object")
            
        except json.JSONDecodeError as e:
            raise CSVProcessingError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"JSON structure analysis failed: {e}")
            raise CSVProcessingError(f"Failed to analyze JSON file: {e}")
    
    def _analyze_jsonl_structure(self, file_path: Path) -> FileStructure:
        """Analyze JSONL (JSON Lines) file structure."""
        try:
            headers = set()
            total_rows = 0
            sample_rows = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict):
                            headers.update(data.keys())
                            total_rows += 1
                            
                            # Collect sample data
                            if len(sample_rows) < 5:
                                sample_rows.append({key: str(data.get(key, "")) for key in data.keys()})
                        else:
                            logger.warning(f"Skipping non-object JSON at line {line_num}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON at line {line_num}: {e}")
                        continue
            
            headers_list = sorted(list(headers))
            
            # Normalize sample rows to have all headers
            normalized_samples = []
            for row in sample_rows:
                normalized_row = {key: row.get(key, "") for key in headers_list}
                normalized_samples.append(normalized_row)
            
            return FileStructure(
                file_format=FileFormat.JSONL,
                headers=headers_list,
                total_rows=total_rows,
                sample_rows=normalized_samples,
                has_header=True
            )
            
        except Exception as e:
            logger.error(f"JSONL structure analysis failed: {e}")
            raise CSVProcessingError(f"Failed to analyze JSONL file: {e}")
    
    def _analyze_csv_like_structure(self, file_path: Path, file_format: FileFormat) -> FileStructure:
        """Analyze CSV-like file structure (CSV, TSV, pipe-delimited, etc.)."""
        try:
            # Step 1: Detect encoding
            encoding_result = self.detect_encoding(file_path)
            logger.debug(f"Encoding detection: {encoding_result.encoding} ({encoding_result.confidence.value})")
            
            # Step 2: Determine delimiter based on format
            if file_format == FileFormat.TSV:
                delimiter_result = DelimiterResult('\t', 1.0, detected_by='format_based')
            elif file_format == FileFormat.SEMICOLON_DELIMITED:
                delimiter_result = DelimiterResult(';', 1.0, detected_by='format_based')
            elif file_format == FileFormat.PIPE_DELIMITED:
                delimiter_result = DelimiterResult('|', 1.0, detected_by='format_based')
            else:
                # Detect delimiter for CSV and unknown formats
                delimiter_result = self.detect_delimiter(file_path, encoding_result.encoding)
            
            logger.debug(f"Delimiter detection: '{delimiter_result.delimiter}' (confidence: {delimiter_result.confidence:.2f})")
            
            # Step 3: Analyze structure with streaming approach
            structure = self._analyze_structure_streaming(
                file_path, 
                encoding_result, 
                delimiter_result
            )
            
            # Update format
            structure.file_format = file_format
            
            return structure
            
        except Exception as e:
            logger.error(f"CSV-like structure analysis failed: {e}")
            raise CSVProcessingError(f"Failed to analyze CSV-like file structure: {e}")
    
    def _analyze_structure_streaming(
        self, 
        file_path: Path, 
        encoding_result: EncodingResult,
        delimiter_result: DelimiterResult,
        sample_rows: int = 5
    ) -> FileStructure:
        """Analyze CSV structure using streaming approach for memory efficiency."""
        
        headers = []
        sample_data = []
        total_rows = 0
        has_header = True
        
        try:
            with open(file_path, 'r', encoding=encoding_result.encoding, newline='') as f:
                # Create CSV reader with detected parameters
                reader = csv.reader(
                    f,
                    delimiter=delimiter_result.delimiter,
                    quotechar=delimiter_result.quote_char
                )
                
                # Read first row (potential header)
                try:
                    first_row = next(reader)
                    headers = [col.strip() for col in first_row]
                    
                    # Detect if first row is actually a header
                    has_header = self._detect_header_row(first_row)
                    
                    if not has_header:
                        # First row is data, generate column names
                        headers = [f"Column_{i+1}" for i in range(len(first_row))]
                        # Add first row to sample data
                        sample_data.append(dict(zip(headers, first_row)))
                        total_rows = 1
                    
                except StopIteration:
                    # Empty file
                    return FileStructure(
                        file_format=FileFormat.CSV,
                        encoding=encoding_result,
                        delimiter=delimiter_result,
                        headers=[],
                        total_rows=0,
                        sample_rows=[],
                        has_header=False
                    )
                
                # Read sample rows and count total
                sample_count = 0
                for row in reader:
                    total_rows += 1
                    
                    if sample_count < sample_rows:
                        if len(row) == len(headers):
                            row_dict = dict(zip(headers, row))
                            sample_data.append(row_dict)
                            sample_count += 1
                        else:
                            # Handle rows with different column counts
                            padded_row = row + [''] * (len(headers) - len(row))
                            row_dict = dict(zip(headers, padded_row[:len(headers)]))
                            sample_data.append(row_dict)
                            sample_count += 1
            
            return FileStructure(
                file_format=FileFormat.CSV,  # Will be updated by caller
                encoding=encoding_result,
                delimiter=delimiter_result,
                headers=headers,
                total_rows=total_rows,
                sample_rows=sample_data,
                has_header=has_header
            )
            
        except Exception as e:
            logger.error(f"Streaming structure analysis failed: {e}")
            raise CSVProcessingError(f"Failed to analyze CSV structure: {e}")
    
    def _detect_header_row(self, first_row: List[str]) -> bool:
        """
        Detect if the first row contains headers or data.
        
        Args:
            first_row: First row of CSV data
            
        Returns:
            True if first row appears to be headers
        """
        if not first_row:
            return False
        
        # Heuristics for header detection
        header_indicators = 0
        total_columns = len(first_row)
        
        for value in first_row:
            value = value.strip().lower()
            
            # Check for common header patterns
            if any(pattern in value for pattern in ['name', 'email', 'phone', 'company', 'address']):
                header_indicators += 1
            
            # Headers typically don't contain @ symbols (emails) or phone patterns
            if '@' in value or re.match(r'[\+\-\(\)\d\s]{8,}', value):
                header_indicators -= 1
            
            # Headers are usually not purely numeric
            if value.replace('.', '').replace('-', '').isdigit():
                header_indicators -= 0.5
        
        # Decision based on ratio of header indicators
        header_ratio = header_indicators / total_columns if total_columns > 0 else 0
        return header_ratio > 0.3
    
    def stream_table_rows(
        self, 
        file_path: Path, 
        structure: Optional[FileStructure] = None,
        chunk_size: int = 1000,
        sheet_name: Optional[str] = None
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream table rows in chunks for memory-efficient processing.
        Supports CSV, Excel, JSON, JSONL, and other formats.
        
        Args:
            file_path: Path to table file
            structure: Pre-analyzed file structure (optional)
            chunk_size: Number of rows per chunk
            sheet_name: Sheet name for Excel files (optional)
            
        Yields:
            Chunks of table rows as dictionaries
        """
        if structure is None:
            structure = self.analyze_file_structure(file_path, sheet_name)
        
        try:
            if structure.file_format in [FileFormat.EXCEL_XLSX, FileFormat.EXCEL_XLS]:
                yield from self._stream_excel_rows(file_path, structure, chunk_size, sheet_name)
            elif structure.file_format == FileFormat.JSON:
                yield from self._stream_json_rows(file_path, structure, chunk_size)
            elif structure.file_format == FileFormat.JSONL:
                yield from self._stream_jsonl_rows(file_path, structure, chunk_size)
            else:
                # Handle CSV-like formats
                yield from self._stream_csv_like_rows(file_path, structure, chunk_size)
                
        except Exception as e:
            logger.error(f"Table streaming failed: {e}")
            raise CSVProcessingError(f"Failed to stream table rows: {e}")
    
    def _stream_excel_rows(self, file_path: Path, structure: FileStructure, chunk_size: int, sheet_name: Optional[str] = None) -> Iterator[List[Dict[str, Any]]]:
        """Stream Excel rows in chunks."""
        try:
            active_sheet = sheet_name or structure.active_sheet
            
            # Use pandas to read in chunks (Excel doesn't support native chunking, so we read all and chunk)
            df = pd.read_excel(file_path, sheet_name=active_sheet, 
                             engine='openpyxl' if structure.file_format == FileFormat.EXCEL_XLSX else 'xlrd')
            df = df.dropna(how='all')
            
            chunk = []
            for index, row in df.iterrows():
                row_dict = {}
                for col in structure.headers:
                    value = row.get(col, "")
                    if pd.isna(value):
                        row_dict[col] = ""
                    else:
                        row_dict[col] = str(value)
                
                row_dict['_row_number'] = index + 1
                chunk.append(row_dict)
                
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
            
            if chunk:
                yield chunk
                
        except Exception as e:
            logger.error(f"Excel streaming failed: {e}")
            raise CSVProcessingError(f"Failed to stream Excel rows: {e}")
    
    def _stream_json_rows(self, file_path: Path, structure: FileStructure, chunk_size: int) -> Iterator[List[Dict[str, Any]]]:
        """Stream JSON rows in chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                chunk = []
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        row_dict = {key: str(item.get(key, "")) for key in structure.headers}
                        row_dict['_row_number'] = i + 1
                        chunk.append(row_dict)
                        
                        if len(chunk) >= chunk_size:
                            yield chunk
                            chunk = []
                
                if chunk:
                    yield chunk
            
            elif isinstance(data, dict):
                # Single object
                row_dict = {key: str(data.get(key, "")) for key in structure.headers}
                row_dict['_row_number'] = 1
                yield [row_dict]
                
        except Exception as e:
            logger.error(f"JSON streaming failed: {e}")
            raise CSVProcessingError(f"Failed to stream JSON rows: {e}")
    
    def _stream_jsonl_rows(self, file_path: Path, structure: FileStructure, chunk_size: int) -> Iterator[List[Dict[str, Any]]]:
        """Stream JSONL rows in chunks."""
        try:
            chunk = []
            row_number = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict):
                            row_number += 1
                            row_dict = {key: str(data.get(key, "")) for key in structure.headers}
                            row_dict['_row_number'] = row_number
                            chunk.append(row_dict)
                            
                            if len(chunk) >= chunk_size:
                                yield chunk
                                chunk = []
                    except json.JSONDecodeError:
                        continue
            
            if chunk:
                yield chunk
                
        except Exception as e:
            logger.error(f"JSONL streaming failed: {e}")
            raise CSVProcessingError(f"Failed to stream JSONL rows: {e}")
    
    def _stream_csv_like_rows(self, file_path: Path, structure: FileStructure, chunk_size: int) -> Iterator[List[Dict[str, Any]]]:
        """Stream CSV-like rows in chunks."""
        try:
            with open(file_path, 'r', encoding=structure.encoding.encoding, newline='') as f:
                reader = csv.reader(
                    f,
                    delimiter=structure.delimiter.delimiter,
                    quotechar=structure.delimiter.quote_char
                )
                
                # Skip header if present
                if structure.has_header:
                    next(reader, None)
                
                chunk = []
                row_number = 1 if structure.has_header else 0
                
                for row in reader:
                    row_number += 1
                    
                    # Handle rows with different column counts
                    if len(row) != len(structure.headers):
                        # Pad or truncate row to match headers
                        if len(row) < len(structure.headers):
                            row.extend([''] * (len(structure.headers) - len(row)))
                        else:
                            row = row[:len(structure.headers)]
                    
                    # Create row dictionary
                    row_dict = dict(zip(structure.headers, row))
                    row_dict['_row_number'] = row_number
                    chunk.append(row_dict)
                    
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                
                # Yield remaining rows
                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.error(f"CSV-like streaming failed: {e}")
            raise CSVProcessingError(f"Failed to stream CSV-like rows: {e}")
    
    # Backward compatibility alias
    def stream_csv_rows(self, file_path: Path, structure: Optional[FileStructure] = None, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        """Backward compatibility method for streaming CSV rows."""
        return self.stream_table_rows(file_path, structure, chunk_size)
    
    def validate_table_comprehensive(
        self, 
        file_path: Path, 
        structure: Optional[FileStructure] = None,
        sheet_name: Optional[str] = None
    ) -> TableValidationReport:
        """
        Comprehensive table validation with detailed error reporting.
        Supports CSV, Excel, JSON, JSONL, and other formats.
        
        Args:
            file_path: Path to table file
            structure: Pre-analyzed file structure (optional)
            sheet_name: Sheet name for Excel files (optional)
            
        Returns:
            Detailed validation report
        """
        if structure is None:
            structure = self.analyze_file_structure(file_path, sheet_name)
        
        report = TableValidationReport(
            total_rows=structure.total_rows, 
            valid_rows=0,
            file_format=structure.file_format
        )
        
        # Validate encoding (for text-based formats)
        if structure.encoding and structure.encoding.confidence == EncodingConfidence.FALLBACK:
            report.encoding_issues.append(
                f"Low confidence encoding detection: {structure.encoding.encoding}"
            )
        
        # Format-specific validation
        if structure.file_format in [FileFormat.EXCEL_XLSX, FileFormat.EXCEL_XLS]:
            if not structure.sheet_names:
                report.format_issues.append("No sheets found in Excel file")
            elif structure.active_sheet not in structure.sheet_names:
                report.format_issues.append(f"Sheet '{structure.active_sheet}' not found in Excel file")
        
        elif structure.file_format in [FileFormat.JSON, FileFormat.JSONL]:
            # JSON-specific validation is handled during structure analysis
            pass
        
        # Validate structure
        if not structure.headers:
            report.structure_issues.append("No columns detected in CSV file")
            return report
        
        if structure.total_rows == 0:
            report.structure_issues.append("CSV file contains no data rows")
            return report
        
        # Validate column mapping
        column_mapping = self._detect_intelligent_column_mapping(structure.headers)
        missing_required = []
        for required_field in ['name', 'company', 'phone', 'email']:
            if required_field not in column_mapping:
                missing_required.append(required_field)
        
        if missing_required:
            report.structure_issues.append(
                f"Cannot map required columns: {', '.join(missing_required)}"
            )
        
        # Validate data rows
        valid_count = 0
        for chunk in self.stream_table_rows(file_path, structure, chunk_size=500, sheet_name=sheet_name):
            for row_data in chunk:
                row_number = row_data.get('_row_number', 0)
                
                # Validate individual row
                row_issues = self._validate_row_comprehensive(row_data, column_mapping, row_number)
                report.issues.extend(row_issues)
                
                if not any(issue.severity == 'error' for issue in row_issues):
                    valid_count += 1
        
        report.valid_rows = valid_count
        
        logger.info(f"Validation complete: {report.valid_rows}/{report.total_rows} valid rows, "
                   f"{report.error_count} errors, {report.warning_count} warnings")
        
        return report
    
    # Backward compatibility alias
    def validate_csv_comprehensive(self, file_path: Path, structure: Optional[FileStructure] = None) -> TableValidationReport:
        """Backward compatibility method for CSV validation."""
        return self.validate_table_comprehensive(file_path, structure)
    
    def _validate_row_comprehensive(
        self, 
        row_data: Dict[str, Any], 
        column_mapping: Dict[str, str],
        row_number: int
    ) -> List[ValidationIssue]:
        """
        Comprehensive validation of a single CSV row using advanced data validator.
        
        Args:
            row_data: Row data dictionary
            column_mapping: Column mapping configuration
            row_number: Row number for error reporting
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Extract customer data using column mapping
        customer_data = {}
        for field, column in column_mapping.items():
            value = row_data.get(column, '').strip() if row_data.get(column) else ''
            customer_data[field] = value
        
        # Use advanced data validator
        validation_result = self.data_validator.validate_customer_data(customer_data)
        
        # Convert validation result to CSV validation issues
        for validator_issue in validation_result.issues:
            # Map severity
            if validator_issue.severity.value == 'error':
                severity = 'error'
            elif validator_issue.severity.value == 'warning':
                severity = 'warning'
            else:
                severity = 'info'
            
            # Get the column name for this field
            column = column_mapping.get(validator_issue.field, validator_issue.field)
            
            csv_issue = ValidationIssue(
                row_number=row_number,
                column=column,
                value=validator_issue.value,
                issue_type=validator_issue.rule_name,
                message=validator_issue.message,
                severity=severity,
                suggestion=validator_issue.suggestion
            )
            issues.append(csv_issue)
        
        # Check for completely empty rows
        if all(not str(v).strip() for v in row_data.values() if not str(v).startswith('_')):
            issues.append(ValidationIssue(
                row_number=row_number,
                column='all',
                value='',
                issue_type='empty_row',
                message="Row is completely empty",
                severity='warning',
                suggestion="Remove empty rows or add data"
            ))
        
        return issues
    
    def validate_customer_data_quality(
        self, 
        customer_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate customer data quality using advanced data validator.
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Comprehensive validation result
        """
        return self.data_validator.validate_customer_data(customer_data)
    
    def get_data_quality_suggestions(
        self, 
        customers: List[Customer]
    ) -> Dict[str, Any]:
        """
        Get data quality suggestions for a list of customers.
        
        Args:
            customers: List of Customer objects
            
        Returns:
            Data quality analysis and suggestions
        """
        # Convert customers to data records
        data_records = [customer.to_dict() for customer in customers]
        
        # Perform batch validation
        batch_result = self.data_validator.validate_batch_data(data_records)
        
        return batch_result
    
    def get_intelligent_column_mapping(
        self, 
        headers: List[str], 
        sample_data: Optional[List[Dict[str, Any]]] = None,
        use_templates: bool = True,
        learn_patterns: bool = True
    ) -> MappingResult:
        """
        Get intelligent column mapping with comprehensive analysis.
        
        Args:
            headers: List of column headers
            sample_data: Sample data for pattern analysis
            use_templates: Whether to use existing templates
            learn_patterns: Whether to learn new patterns from data
            
        Returns:
            Complete mapping result with confidence scores and suggestions
        """
        return self.column_mapper.map_columns(
            headers=headers,
            sample_data=sample_data,
            use_templates=use_templates,
            learn_patterns=learn_patterns
        )
    
    def _detect_intelligent_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """
        Intelligent column mapping using pattern recognition and scoring (backward compatibility).
        
        Args:
            headers: List of column headers
            
        Returns:
            Mapping of required fields to column names
        """
        # Use the new intelligent mapper but return simple mapping for backward compatibility
        mapping_result = self.column_mapper.map_columns(headers, use_templates=True, learn_patterns=False)
        
        # Convert to simple mapping format
        simple_mapping = {}
        for field, column_mapping in mapping_result.mappings.items():
            simple_mapping[field] = column_mapping.source_column
        
        return simple_mapping
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings using simple algorithm."""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        # Simple character-based similarity
        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if len(s1) > len(s2) else s1
        
        if len(longer) == 0:
            return 1.0
        
        # Count matching characters
        matches = sum(1 for c in shorter if c in longer)
        return matches / len(longer)
    
    def load_customers_advanced(
        self, 
        file_path: Path, 
        column_mapping: Optional[Dict[str, str]] = None,
        structure: Optional[FileStructure] = None,
        validate_data: bool = True,
        stream_processing: bool = False,
        sheet_name: Optional[str] = None
    ) -> Tuple[List[Customer], TableValidationReport]:
        """
        Advanced customer loading with comprehensive validation and error reporting.
        Supports CSV, Excel, JSON, JSONL, and other formats.
        
        Args:
            file_path: Path to table file
            column_mapping: Manual column mapping (optional)
            structure: Pre-analyzed file structure (optional)
            validate_data: Whether to perform comprehensive validation
            stream_processing: Use streaming for large files
            sheet_name: Sheet name for Excel files (optional)
            
        Returns:
            Tuple of (valid customers, validation report)
        """
        try:
            # Analyze file structure if not provided
            if structure is None:
                structure = self.analyze_file_structure(file_path, sheet_name)
            
            # Get column mapping
            if column_mapping is None:
                column_mapping = self._detect_intelligent_column_mapping(structure.headers)
            
            # Validate column mapping
            required_fields = ['name', 'company', 'phone', 'email']
            missing_fields = [field for field in required_fields if field not in column_mapping]
            
            if missing_fields:
                raise CSVProcessingError(
                    f"Missing required columns: {', '.join(missing_fields)}. "
                    f"Available columns: {', '.join(structure.headers)}"
                )
            
            # Perform comprehensive validation if requested
            validation_report = None
            if validate_data:
                validation_report = self.validate_table_comprehensive(file_path, structure, sheet_name)
            else:
                validation_report = TableValidationReport(
                    total_rows=structure.total_rows,
                    valid_rows=0,  # Will be updated during processing
                    file_format=structure.file_format
                )
            
            # Load customers using appropriate method
            if stream_processing or structure.total_rows > 5000:
                customers = self._load_customers_streaming(file_path, structure, column_mapping, validation_report, sheet_name)
            else:
                customers = self._load_customers_batch(file_path, structure, column_mapping, validation_report, sheet_name)
            
            validation_report.valid_rows = len(customers)
            
            logger.info(f"Loaded {len(customers)} customers from {structure.total_rows} rows "
                       f"({validation_report.success_rate:.1f}% success rate)")
            
            return customers, validation_report
            
        except Exception as e:
            logger.error(f"Advanced customer loading failed: {e}")
            raise CSVProcessingError(f"Failed to load customers: {e}")
    
    def _load_customers_streaming(
        self, 
        file_path: Path, 
        structure: FileStructure,
        column_mapping: Dict[str, str],
        validation_report: TableValidationReport,
        sheet_name: Optional[str] = None
    ) -> List[Customer]:
        """Load customers using streaming approach for memory efficiency."""
        customers = []
        
        for chunk in self.stream_table_rows(file_path, structure, chunk_size=1000, sheet_name=sheet_name):
            for row_data in chunk:
                try:
                    # Extract customer data
                    customer_data = {}
                    for field, column in column_mapping.items():
                        value = row_data.get(column, '').strip() if row_data.get(column) else ''
                        customer_data[field] = value
                    
                    # Create customer
                    customer = Customer.from_dict(customer_data)
                    customers.append(customer)
                    
                except ValidationError as e:
                    # Validation errors are already captured in comprehensive validation
                    logger.debug(f"Skipping invalid customer at row {row_data.get('_row_number', 'unknown')}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error processing row {row_data.get('_row_number', 'unknown')}: {e}")
                    continue
        
        return customers
    
    def _load_customers_batch(
        self, 
        file_path: Path, 
        structure: FileStructure,
        column_mapping: Dict[str, str],
        validation_report: TableValidationReport,
        sheet_name: Optional[str] = None
    ) -> List[Customer]:
        """Load customers using batch approach for smaller files."""
        customers = []
        
        try:
            # Read file based on format
            if structure.file_format in [FileFormat.EXCEL_XLSX, FileFormat.EXCEL_XLS]:
                active_sheet = sheet_name or structure.active_sheet
                df = pd.read_excel(
                    file_path, 
                    sheet_name=active_sheet,
                    engine='openpyxl' if structure.file_format == FileFormat.EXCEL_XLSX else 'xlrd'
                )
            elif structure.file_format == FileFormat.JSON:
                df = pd.read_json(file_path)
            elif structure.file_format == FileFormat.JSONL:
                df = pd.read_json(file_path, lines=True)
            else:
                # CSV-like formats
                df = pd.read_csv(
                    file_path, 
                    encoding=structure.encoding.encoding,
                    delimiter=structure.delimiter.delimiter,
                    quotechar=structure.delimiter.quote_char
                )
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            for index, row in df.iterrows():
                try:
                    # Extract customer data using column mapping
                    customer_data = {}
                    for field, column in column_mapping.items():
                        if column in row:
                            value = row[column]
                            # Handle NaN values
                            if pd.isna(value):
                                customer_data[field] = ""
                            else:
                                customer_data[field] = str(value).strip()
                        else:
                            customer_data[field] = ""
                    
                    # Create and validate customer
                    customer = Customer.from_dict(customer_data)
                    customers.append(customer)
                    
                except ValidationError as e:
                    # Validation errors are already captured in comprehensive validation
                    logger.debug(f"Skipping invalid customer at row {index + 2}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error processing row {index + 2}: {e}")
                    continue
            
            return customers
            
        except Exception as e:
            logger.error(f"Batch customer loading failed: {e}")
            raise CSVProcessingError(f"Failed to load customers in batch mode: {e}")
    
    def load_customers(
        self, 
        file_path: Path, 
        column_mapping: Optional[Dict[str, str]] = None,
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None
    ) -> Tuple[List[Customer], List[Dict[str, Any]]]:
        """
        Load customers from CSV file (backward compatibility method).
        
        Args:
            file_path: Path to CSV file
            column_mapping: Manual column mapping (optional)
            encoding: File encoding (optional, will auto-detect)
            delimiter: CSV delimiter (optional, will auto-detect)
            
        Returns:
            Tuple of (valid customers, error records)
        """
        try:
            # Use advanced loading method
            customers, validation_report = self.load_customers_advanced(
                file_path=file_path,
                column_mapping=column_mapping,
                validate_data=True,
                stream_processing=False
            )
            
            # Convert validation report to old error format for backward compatibility
            errors = []
            for issue in validation_report.issues:
                if issue.severity == 'error':
                    error_record = {
                        'row_number': issue.row_number,
                        'column': issue.column,
                        'value': issue.value,
                        'error': issue.message
                    }
                    errors.append(error_record)
            
            logger.info(f"Loaded {len(customers)} valid customers, {len(errors)} errors")
            return customers, errors
            
        except Exception as e:
            logger.error(f"Failed to load customers from CSV: {e}")
            raise CSVProcessingError(f"Failed to load customers from CSV: {e}")
    
    def validate_table_format(self, file_path: Path, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate table file format and structure supporting multiple formats.
        
        Args:
            file_path: Path to table file
            sheet_name: Sheet name for Excel files (optional)
            
        Returns:
            Validation results with format information
        """
        try:
            if not file_path.exists():
                return {
                    'valid': False,
                    'errors': ['File does not exist']
                }
            
            # Detect format
            file_format = self.detect_file_format(file_path)
            
            # Check if format is supported
            supported_extensions = list(self.FORMAT_EXTENSIONS.keys())
            if file_path.suffix.lower() not in supported_extensions and file_format == FileFormat.UNKNOWN:
                return {
                    'valid': False,
                    'errors': [f'Unsupported file format. Supported formats: {", ".join(supported_extensions)}']
                }
            
            # Use advanced validation
            structure = self.analyze_file_structure(file_path, sheet_name)
            validation_report = self.validate_table_comprehensive(file_path, structure, sheet_name)
            
            errors = []
            warnings = []
            
            # Convert structure issues to legacy format
            errors.extend(validation_report.structure_issues)
            errors.extend(validation_report.format_issues)
            warnings.extend(validation_report.encoding_issues)
            
            # Check for critical validation errors
            if validation_report.error_count > validation_report.total_rows * 0.5:
                errors.append(f"Too many validation errors: {validation_report.error_count} out of {validation_report.total_rows} rows")
            
            # Create analysis format
            column_mapping = self._detect_intelligent_column_mapping(structure.headers)
            analysis = {
                'file_format': file_format.value,
                'encoding': structure.encoding.encoding if structure.encoding else 'N/A',
                'delimiter': structure.delimiter.delimiter if structure.delimiter else 'N/A',
                'columns': structure.headers,
                'sample_data': structure.sample_rows,
                'column_mapping': column_mapping,
                'total_rows': structure.total_rows,
                'required_columns_found': all(field in column_mapping for field in ['name', 'company', 'phone', 'email']),
                'sheet_names': structure.sheet_names,
                'active_sheet': structure.active_sheet
            }
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Failed to validate file: {e}"]
            }
    
    # Backward compatibility alias
    def validate_csv_format(self, file_path: Path) -> Dict[str, Any]:
        """Backward compatibility method for CSV format validation."""
        return self.validate_table_format(file_path)
    
    def export_template(self, file_path: Path, include_examples: bool = True) -> None:
        """
        Export a CSV template file with correct column headers.
        
        Args:
            file_path: Path where to save the template
            include_examples: Whether to include example data
        """
        try:
            if include_examples:
                template_data = [
                    {
                        'name': 'John Doe',
                        'company': 'Example Corp',
                        'phone': '+1-555-0123',
                        'email': 'john.doe@example.com'
                    },
                    {
                        'name': 'Jane Smith',
                        'company': 'Sample Inc',
                        'phone': '+1-555-0456',
                        'email': 'jane.smith@sample.com'
                    },
                    {
                        'name': 'Carlos Rodriguez',
                        'company': 'Demo LLC',
                        'phone': '+1-555-0789',
                        'email': 'carlos.rodriguez@demo.com'
                    }
                ]
            else:
                # Just headers
                template_data = [
                    {
                        'name': '',
                        'company': '',
                        'phone': '',
                        'email': ''
                    }
                ]
            
            df = pd.DataFrame(template_data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            logger.info(f"Exported CSV template to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export CSV template: {e}")
            raise CSVProcessingError(f"Failed to export CSV template: {e}")
    
    def get_file_preview(self, file_path: Path, max_rows: int = 10) -> Dict[str, Any]:
        """
        Get a preview of CSV file contents for user review.
        
        Args:
            file_path: Path to CSV file
            max_rows: Maximum number of rows to preview
            
        Returns:
            Preview data with structure information
        """
        try:
            structure = self.analyze_file_structure(file_path)
            
            # Get more sample data if needed
            preview_rows = structure.sample_rows[:max_rows]
            if len(preview_rows) < max_rows and structure.total_rows > len(preview_rows):
                # Get additional rows
                additional_needed = min(max_rows - len(preview_rows), structure.total_rows - len(preview_rows))
                for chunk in self.stream_table_rows(file_path, structure, chunk_size=additional_needed):
                    for row in chunk[:additional_needed]:
                        if '_row_number' in row:
                            del row['_row_number']
                        preview_rows.append(row)
                        if len(preview_rows) >= max_rows:
                            break
                    break
            
            column_mapping = self._detect_intelligent_column_mapping(structure.headers)
            
            return {
                'structure': {
                    'encoding': structure.encoding.encoding,
                    'encoding_confidence': structure.encoding.confidence.value,
                    'delimiter': structure.delimiter.delimiter,
                    'total_rows': structure.total_rows,
                    'total_columns': len(structure.headers)
                },
                'headers': structure.headers,
                'column_mapping': column_mapping,
                'preview_rows': preview_rows,
                'mapping_confidence': self._calculate_mapping_confidence(column_mapping, structure.headers)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate file preview: {e}")
            raise CSVProcessingError(f"Failed to generate file preview: {e}")
    
    def _calculate_mapping_confidence(self, column_mapping: Dict[str, str], headers: List[str]) -> Dict[str, float]:
        """Calculate confidence scores for column mappings."""
        confidence = {}
        
        for field, mapped_column in column_mapping.items():
            if field in self.COLUMN_MAPPINGS:
                config = self.COLUMN_MAPPINGS[field]
                header_lower = mapped_column.lower().strip()
                
                # Check exact matches
                if header_lower in [name.lower() for name in config['exact']]:
                    confidence[field] = 1.0
                else:
                    # Check pattern matches
                    max_pattern_score = 0.0
                    for pattern in config['patterns']:
                        if re.search(pattern.lower(), header_lower):
                            max_pattern_score = max(max_pattern_score, 0.8)
                    
                    # Check fuzzy matches
                    max_fuzzy_score = 0.0
                    for exact_name in config['exact']:
                        similarity = self._calculate_string_similarity(header_lower, exact_name.lower())
                        if similarity > 0.7:
                            max_fuzzy_score = max(max_fuzzy_score, similarity * 0.9)
                    
                    confidence[field] = max(max_pattern_score, max_fuzzy_score)
            else:
                confidence[field] = 0.5  # Default confidence for unknown fields
        
        return confidence
    
    def create_mapping_template(
        self, 
        name: str, 
        description: str, 
        column_mappings: Dict[str, str]
    ) -> None:
        """
        Create a reusable mapping template from current column mappings.
        
        Args:
            name: Template name
            description: Template description
            column_mappings: Dictionary of field -> column mappings
        """
        # Convert simple mappings to ColumnMapping objects
        mappings = {}
        for field, column in column_mappings.items():
            mappings[field] = ColumnMapping(
                source_column=column,
                target_field=field,
                confidence=MappingConfidence.HIGH,
                confidence_score=1.0,
                detection_method='user_defined',
                user_confirmed=True
            )
        
        template = self.column_mapper.create_mapping_template(name, description, mappings)
        logger.info(f"Created mapping template: {name}")
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of available mapping templates.
        
        Returns:
            List of template information dictionaries
        """
        templates = []
        for template in self.column_mapper.templates:
            templates.append({
                'name': template.name,
                'description': template.description,
                'mappings': template.mappings,
                'usage_count': template.usage_count,
                'success_rate': template.success_rate,
                'created_at': template.created_at
            })
        
        return templates
    
    def apply_mapping_template(self, template_name: str, headers: List[str]) -> Optional[Dict[str, str]]:
        """
        Apply a specific mapping template to headers.
        
        Args:
            template_name: Name of the template to apply
            headers: List of column headers
            
        Returns:
            Column mappings if template can be applied, None otherwise
        """
        # Find the template
        template = None
        for t in self.column_mapper.templates:
            if t.name == template_name:
                template = t
                break
        
        if not template:
            logger.warning(f"Template '{template_name}' not found")
            return None
        
        # Try to apply the template
        mappings = {}
        for field, column_pattern in template.mappings.items():
            # Find matching column
            for header in headers:
                if self.column_mapper._matches_template_pattern(
                    header, column_pattern, template.patterns.get(field, [])
                ):
                    mappings[field] = header
                    break
        
        # Update template usage
        success = len(mappings) >= len(template.mappings) * 0.7  # 70% success threshold
        self.column_mapper.update_template_usage(template_name, success)
        
        return mappings if mappings else None
    
    def get_mapping_suggestions(
        self, 
        headers: List[str], 
        current_mappings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get intelligent suggestions for column mapping.
        
        Args:
            headers: List of column headers
            current_mappings: Current column mappings (optional)
            
        Returns:
            Dictionary with mapping suggestions and analysis
        """
        # Get intelligent mapping
        mapping_result = self.get_intelligent_column_mapping(headers)
        
        # Determine unmapped columns and missing fields
        if current_mappings:
            mapped_columns = set(current_mappings.values())
            unmapped_columns = [h for h in headers if h not in mapped_columns]
            missing_fields = []
            for field in ['name', 'company', 'phone', 'email']:
                if field not in current_mappings:
                    missing_fields.append(field)
        else:
            unmapped_columns = mapping_result.unmapped_columns
            missing_fields = mapping_result.missing_required_fields
        
        # Get suggestions for unmapped columns
        suggestions = self.column_mapper.get_mapping_suggestions(unmapped_columns, missing_fields)
        
        return {
            'automatic_mappings': {field: mapping.source_column for field, mapping in mapping_result.mappings.items()},
            'confidence_scores': {field: mapping.confidence_score for field, mapping in mapping_result.mappings.items()},
            'unmapped_columns': unmapped_columns,
            'missing_fields': missing_fields,
            'suggestions': suggestions,
            'suggested_templates': [
                {'name': t.name, 'description': t.description, 'success_rate': t.success_rate}
                for t in mapping_result.suggested_templates
            ],
            'transformation_suggestions': mapping_result.transformation_suggestions,
            'overall_confidence': mapping_result.confidence_score
        }
    
    def validate_column_mapping(
        self, 
        mappings: Dict[str, str], 
        headers: List[str],
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validate a proposed column mapping.
        
        Args:
            mappings: Dictionary of field -> column mappings
            headers: List of available column headers
            sample_data: Sample data for validation
            
        Returns:
            Validation results with issues and suggestions
        """
        validation_issues = self.column_mapper.validate_mapping(mappings, sample_data)
        
        # Additional validation
        issues = dict(validation_issues)
        
        # Check if all mapped columns exist in headers
        for field, column in mappings.items():
            if column not in headers:
                field_issues = issues.setdefault(field, [])
                field_issues.append(f"Column '{column}' not found in CSV headers")
        
        # Calculate validation score
        total_issues = sum(len(issue_list) for issue_list in issues.values())
        validation_score = max(0.0, 1.0 - (total_issues * 0.1))  # Each issue reduces score by 0.1
        
        return {
            'valid': total_issues == 0,
            'issues': issues,
            'validation_score': validation_score,
            'total_issues': total_issues
        }


# Backward compatibility aliases
AdvancedCSVProcessor = AdvancedTableProcessor
CSVProcessor = AdvancedTableProcessor
