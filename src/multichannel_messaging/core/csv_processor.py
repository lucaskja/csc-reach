"""
CSV file processing for Multi-Channel Bulk Messaging System.
"""

import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from io import StringIO

from .models import Customer
from ..utils.exceptions import CSVProcessingError, ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CSVProcessor:
    """CSV file processor for customer data."""
    
    # Standard column mappings
    COLUMN_MAPPINGS = {
        'name': ['name', 'customer_name', 'full_name', 'client_name', 'nome', 'nombre'],
        'company': ['company', 'company_name', 'organization', 'org', 'empresa', 'compañía'],
        'phone': ['phone', 'telephone', 'mobile', 'cell', 'telefone', 'teléfono'],
        'email': ['email', 'email_address', 'e-mail', 'mail', 'correo']
    }
    
    def __init__(self):
        """Initialize CSV processor."""
        self.detected_encoding = None
        self.detected_delimiter = None
        self.column_mapping = {}
    
    def detect_encoding(self, file_path: Path) -> str:
        """
        Detect file encoding.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Detected encoding
        """
        import chardet
        
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                logger.debug(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                
                # Fallback to common encodings if confidence is low
                if confidence < 0.7:
                    for fallback in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            with open(file_path, 'r', encoding=fallback) as test_f:
                                test_f.read(1000)
                            encoding = fallback
                            logger.debug(f"Using fallback encoding: {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                
                self.detected_encoding = encoding
                return encoding
                
        except Exception as e:
            logger.warning(f"Failed to detect encoding: {e}")
            self.detected_encoding = 'utf-8'
            return 'utf-8'
    
    def detect_delimiter(self, file_path: Path, encoding: str = 'utf-8') -> str:
        """
        Detect CSV delimiter.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding
            
        Returns:
            Detected delimiter
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                sample = f.read(1024)
                
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            logger.debug(f"Detected delimiter: '{delimiter}'")
            self.detected_delimiter = delimiter
            return delimiter
            
        except Exception as e:
            logger.warning(f"Failed to detect delimiter: {e}")
            self.detected_delimiter = ','
            return ','
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze CSV file structure.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            File analysis results
        """
        try:
            # Detect encoding and delimiter
            encoding = self.detect_encoding(file_path)
            delimiter = self.detect_delimiter(file_path, encoding)
            
            # Read first few rows to analyze structure
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, nrows=5)
            
            columns = df.columns.tolist()
            sample_data = df.head().to_dict('records')
            
            # Detect column mappings
            column_mapping = self._detect_column_mapping(columns)
            
            analysis = {
                'encoding': encoding,
                'delimiter': delimiter,
                'columns': columns,
                'sample_data': sample_data,
                'column_mapping': column_mapping,
                'total_rows': len(df),
                'required_columns_found': all(field in column_mapping for field in ['name', 'company', 'phone', 'email'])
            }
            
            logger.info(f"Analyzed CSV file: {len(columns)} columns, {len(df)} rows (sample)")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze CSV file: {e}")
            raise CSVProcessingError(f"Failed to analyze CSV file: {e}")
    
    def _detect_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """
        Detect column mapping based on column names.
        
        Args:
            columns: List of column names
            
        Returns:
            Mapping of required fields to column names
        """
        mapping = {}
        columns_lower = [col.lower().strip() for col in columns]
        
        for field, possible_names in self.COLUMN_MAPPINGS.items():
            for possible_name in possible_names:
                if possible_name.lower() in columns_lower:
                    # Find the original column name
                    original_col = columns[columns_lower.index(possible_name.lower())]
                    mapping[field] = original_col
                    break
        
        logger.debug(f"Detected column mapping: {mapping}")
        self.column_mapping = mapping
        return mapping
    
    def load_customers(
        self, 
        file_path: Path, 
        column_mapping: Optional[Dict[str, str]] = None,
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None
    ) -> Tuple[List[Customer], List[Dict[str, Any]]]:
        """
        Load customers from CSV file.
        
        Args:
            file_path: Path to CSV file
            column_mapping: Manual column mapping (optional)
            encoding: File encoding (optional, will auto-detect)
            delimiter: CSV delimiter (optional, will auto-detect)
            
        Returns:
            Tuple of (valid customers, error records)
        """
        try:
            # Use provided parameters or detect automatically
            if not encoding:
                encoding = self.detect_encoding(file_path)
            if not delimiter:
                delimiter = self.detect_delimiter(file_path, encoding)
            if not column_mapping:
                # Analyze file to get column mapping
                analysis = self.analyze_file(file_path)
                column_mapping = analysis['column_mapping']
            
            # Validate column mapping
            required_fields = ['name', 'company', 'phone', 'email']
            missing_fields = [field for field in required_fields if field not in column_mapping]
            
            if missing_fields:
                raise CSVProcessingError(
                    f"Missing required columns: {', '.join(missing_fields)}. "
                    f"Available columns: {', '.join(column_mapping.values())}"
                )
            
            # Read CSV file
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            customers = []
            errors = []
            
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
                    error_record = {
                        'row_number': index + 2,  # +2 because pandas is 0-indexed and CSV has header
                        'data': row.to_dict(),
                        'error': str(e)
                    }
                    errors.append(error_record)
                    logger.warning(f"Invalid customer data at row {index + 2}: {e}")
                
                except Exception as e:
                    error_record = {
                        'row_number': index + 2,
                        'data': row.to_dict(),
                        'error': f"Unexpected error: {e}"
                    }
                    errors.append(error_record)
                    logger.error(f"Unexpected error processing row {index + 2}: {e}")
            
            logger.info(f"Loaded {len(customers)} valid customers, {len(errors)} errors")
            return customers, errors
            
        except Exception as e:
            logger.error(f"Failed to load customers from CSV: {e}")
            raise CSVProcessingError(f"Failed to load customers from CSV: {e}")
    
    def validate_csv_format(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate CSV file format and structure.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Validation results
        """
        try:
            if not file_path.exists():
                return {
                    'valid': False,
                    'errors': ['File does not exist']
                }
            
            if file_path.suffix.lower() not in ['.csv', '.txt']:
                return {
                    'valid': False,
                    'errors': ['File must be a CSV file (.csv or .txt)']
                }
            
            # Try to analyze the file
            analysis = self.analyze_file(file_path)
            
            errors = []
            warnings = []
            
            # Check if required columns can be mapped
            if not analysis['required_columns_found']:
                missing = []
                for field in ['name', 'company', 'phone', 'email']:
                    if field not in analysis['column_mapping']:
                        missing.append(field)
                errors.append(f"Cannot map required columns: {', '.join(missing)}")
            
            # Check if file has data
            if analysis['total_rows'] == 0:
                errors.append("File appears to be empty")
            
            # Check encoding issues
            if analysis['encoding'] not in ['utf-8', 'ascii']:
                warnings.append(f"File encoding is {analysis['encoding']}, which may cause issues")
            
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
    
    def export_template(self, file_path: Path) -> None:
        """
        Export a CSV template file with correct column headers.
        
        Args:
            file_path: Path where to save the template
        """
        try:
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
                }
            ]
            
            df = pd.DataFrame(template_data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            logger.info(f"Exported CSV template to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export CSV template: {e}")
            raise CSVProcessingError(f"Failed to export CSV template: {e}")
