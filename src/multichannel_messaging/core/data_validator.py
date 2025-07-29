"""
Advanced data validation framework with comprehensive email, phone, and business rule validation.
"""

import re
import socket
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse

from ..utils.logger import get_logger
from ..utils.exceptions import CSVProcessingError

logger = get_logger(__name__)

# Optional dependencies with graceful fallbacks
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    logger.warning("DNS resolver not available - domain validation will be limited")

try:
    import phonenumbers
    from phonenumbers import NumberParseException, PhoneNumberFormat
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    logger.warning("phonenumbers library not available - phone validation will be basic")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..utils.exceptions import ValidationError


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Validation categories."""
    FORMAT = "format"
    DOMAIN = "domain"
    BUSINESS_RULE = "business_rule"
    DATA_QUALITY = "data_quality"
    CONSISTENCY = "consistency"


@dataclass
class ValidationIssue:
    """Individual validation issue with detailed information."""
    field: str
    value: Any
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    suggestion: Optional[str] = None
    confidence: float = 1.0
    rule_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'field': self.field,
            'value': str(self.value),
            'severity': self.severity.value,
            'category': self.category.value,
            'message': self.message,
            'suggestion': self.suggestion,
            'confidence': self.confidence,
            'rule_name': self.rule_name
        }


@dataclass
class ValidationResult:
    """Complete validation result for a data record."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    quality_score: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR])
    
    @property
    def warning_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'is_valid': self.is_valid,
            'issues': [issue.to_dict() for issue in self.issues],
            'quality_score': self.quality_score,
            'suggestions': self.suggestions,
            'error_count': self.error_count,
            'warning_count': self.warning_count
        }


class EmailValidator:
    """Advanced email validation with domain checking and suggestions."""
    
    def __init__(self):
        """Initialize email validator."""
        # Common email domain typos and their corrections
        self.domain_corrections = {
            'gmail.co': 'gmail.com',
            'gmail.con': 'gmail.com',
            'gmai.com': 'gmail.com',
            'yahoo.co': 'yahoo.com',
            'yahoo.con': 'yahoo.com',
            'hotmail.co': 'hotmail.com',
            'hotmail.con': 'hotmail.com',
            'outlook.co': 'outlook.com',
            'outlook.con': 'outlook.com',
            'aol.co': 'aol.com',
            'msn.co': 'msn.com',
        }
        
        # Cache for domain validation results
        self._domain_cache: Dict[str, bool] = {}
    
    def validate_email(self, email: str, check_domain: bool = True) -> List[ValidationIssue]:
        """
        Comprehensive email validation.
        
        Args:
            email: Email address to validate
            check_domain: Whether to perform domain validation
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not email or not email.strip():
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Email address is required",
                rule_name='email_required'
            ))
            return issues
        
        email = email.strip().lower()
        
        # Basic format validation
        format_issues = self._validate_email_format(email)
        issues.extend(format_issues)
        
        if format_issues:
            return issues  # Don't continue if format is invalid
        
        # Domain validation
        if check_domain:
            domain_issues = self._validate_email_domain(email)
            issues.extend(domain_issues)
        
        # Business rule validation
        business_issues = self._validate_email_business_rules(email)
        issues.extend(business_issues)
        
        return issues
    
    def _validate_email_format(self, email: str) -> List[ValidationIssue]:
        """Validate email format using comprehensive regex."""
        issues = []
        
        # RFC 5322 compliant regex (simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            suggestion = self._suggest_email_fix(email)
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message=f"Invalid email format: {email}",
                suggestion=suggestion,
                rule_name='email_format'
            ))
            return issues
        
        # Additional format checks
        local, domain = email.split('@', 1)
        
        # Local part validation
        if len(local) > 64:
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Email local part too long (max 64 characters)",
                rule_name='email_local_length'
            ))
        
        if local.startswith('.') or local.endswith('.') or '..' in local:
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Invalid dots in email local part",
                rule_name='email_local_dots'
            ))
        
        # Domain part validation
        if len(domain) > 255:
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Email domain too long (max 255 characters)",
                rule_name='email_domain_length'
            ))
        
        if domain.startswith('.') or domain.endswith('.') or '..' in domain:
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Invalid dots in email domain",
                rule_name='email_domain_dots'
            ))
        
        return issues
    
    def _validate_email_domain(self, email: str) -> List[ValidationIssue]:
        """Validate email domain existence and configuration."""
        issues = []
        
        try:
            domain = email.split('@')[1]
            
            # Check cache first
            if domain in self._domain_cache:
                if not self._domain_cache[domain]:
                    issues.append(ValidationIssue(
                        field='email',
                        value=email,
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.DOMAIN,
                        message=f"Email domain does not exist: {domain}",
                        rule_name='email_domain_exists'
                    ))
                return issues
            
            # Check for common typos first
            corrected_domain = self.domain_corrections.get(domain)
            if corrected_domain:
                issues.append(ValidationIssue(
                    field='email',
                    value=email,
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DOMAIN,
                    message=f"Possible domain typo: {domain}",
                    suggestion=f"Did you mean: {email.replace(domain, corrected_domain)}?",
                    rule_name='email_domain_typo'
                ))
            
            # DNS validation (if available)
            if DNS_AVAILABLE:
                try:
                    # Check MX record
                    mx_records = dns.resolver.resolve(domain, 'MX')
                    if not mx_records:
                        issues.append(ValidationIssue(
                            field='email',
                            value=email,
                            severity=ValidationSeverity.WARNING,
                            category=ValidationCategory.DOMAIN,
                            message=f"No MX record found for domain: {domain}",
                            rule_name='email_domain_mx'
                        ))
                    
                    self._domain_cache[domain] = True
                    
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    issues.append(ValidationIssue(
                        field='email',
                        value=email,
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.DOMAIN,
                        message=f"Email domain does not exist: {domain}",
                        rule_name='email_domain_exists'
                    ))
                    self._domain_cache[domain] = False
                    
                except Exception as e:
                    logger.debug(f"DNS validation failed for {domain}: {e}")
                    # Don't add error for DNS lookup failures, just log
            else:
                # Fallback: basic socket-based domain check
                try:
                    socket.gethostbyname(domain)
                    self._domain_cache[domain] = True
                except socket.gaierror:
                    issues.append(ValidationIssue(
                        field='email',
                        value=email,
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.DOMAIN,
                        message=f"Cannot resolve domain: {domain}",
                        rule_name='email_domain_resolve'
                    ))
                    self._domain_cache[domain] = False
                
        except Exception as e:
            logger.warning(f"Domain validation failed for {email}: {e}")
        
        return issues
    
    def _validate_email_business_rules(self, email: str) -> List[ValidationIssue]:
        """Apply business rules for email validation."""
        issues = []
        
        # Check for disposable email domains
        disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org'
        }
        
        domain = email.split('@')[1]
        if domain in disposable_domains:
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.BUSINESS_RULE,
                message=f"Disposable email domain detected: {domain}",
                suggestion="Consider requesting a permanent email address",
                rule_name='email_disposable_domain'
            ))
        
        # Check for role-based emails
        local_part = email.split('@')[0]
        role_based = {
            'admin', 'administrator', 'info', 'support', 'help',
            'sales', 'marketing', 'noreply', 'no-reply', 'webmaster'
        }
        
        if local_part in role_based:
            issues.append(ValidationIssue(
                field='email',
                value=email,
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.BUSINESS_RULE,
                message=f"Role-based email address: {email}",
                suggestion="Personal email addresses are preferred for individual contacts",
                rule_name='email_role_based'
            ))
        
        return issues
    
    def _suggest_email_fix(self, email: str) -> str:
        """Suggest fixes for invalid email addresses."""
        if not email:
            return "Provide a valid email address (example: user@domain.com)"
        
        email = email.strip()
        
        # Check for missing @
        if '@' not in email:
            return "Email must contain @ symbol (example: user@domain.com)"
        
        # Check for multiple @
        if email.count('@') > 1:
            return "Email should contain only one @ symbol"
        
        # Check for missing domain
        parts = email.split('@')
        if len(parts) != 2 or not parts[1]:
            return "Email must have a domain after @ (example: user@domain.com)"
        
        domain = parts[1]
        if '.' not in domain:
            return "Email domain must contain a dot (example: user@domain.com)"
        
        # Check for common typos
        for typo, correction in self.domain_corrections.items():
            if typo in domain:
                suggested = email.replace(typo, correction)
                return f"Did you mean: {suggested}?"
        
        return "Check email format (example: user@domain.com)"


class PhoneValidator:
    """Advanced international phone number validation and formatting."""
    
    def __init__(self):
        """Initialize phone validator."""
        # Common country codes and their patterns
        self.country_patterns = {
            'US': r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$',
            'UK': r'^\+?44[1-9]\d{8,9}$',
            'CA': r'^\+?1[2-9]\d{2}[2-9]\d{2}\d{4}$',
            'AU': r'^\+?61[2-478]\d{8}$',
            'DE': r'^\+?49[1-9]\d{10,11}$',
            'FR': r'^\+?33[1-9]\d{8}$',
            'BR': r'^\+?55[1-9]\d{10}$',
            'MX': r'^\+?52[1-9]\d{9}$',
        }
    
    def validate_phone(self, phone: str, default_country: str = 'US') -> List[ValidationIssue]:
        """
        Comprehensive phone number validation.
        
        Args:
            phone: Phone number to validate
            default_country: Default country code for parsing
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not phone or not phone.strip():
            issues.append(ValidationIssue(
                field='phone',
                value=phone,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Phone number is required",
                rule_name='phone_required'
            ))
            return issues
        
        phone = phone.strip()
        
        # Basic format validation
        format_issues = self._validate_phone_format(phone)
        issues.extend(format_issues)
        
        # Advanced validation with phonenumbers library (if available)
        if PHONENUMBERS_AVAILABLE:
            try:
                parsed_number = phonenumbers.parse(phone, default_country)
                
                # Validate the parsed number
                if not phonenumbers.is_valid_number(parsed_number):
                    issues.append(ValidationIssue(
                        field='phone',
                        value=phone,
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.FORMAT,
                        message=f"Invalid phone number: {phone}",
                        suggestion=self._suggest_phone_fix(phone),
                        rule_name='phone_invalid'
                    ))
                else:
                    # Check if it's a possible number
                    if not phonenumbers.is_possible_number(parsed_number):
                        issues.append(ValidationIssue(
                            field='phone',
                            value=phone,
                            severity=ValidationSeverity.WARNING,
                            category=ValidationCategory.FORMAT,
                            message=f"Phone number may not be valid: {phone}",
                            rule_name='phone_possible'
                        ))
                    
                    # Format suggestions
                    formatted_international = phonenumbers.format_number(parsed_number, PhoneNumberFormat.INTERNATIONAL)
                    if phone != formatted_international:
                        issues.append(ValidationIssue(
                            field='phone',
                            value=phone,
                            severity=ValidationSeverity.INFO,
                            category=ValidationCategory.FORMAT,
                            message="Phone number formatting suggestion",
                            suggestion=f"Consider using international format: {formatted_international}",
                            rule_name='phone_format_suggestion'
                        ))
            
            except NumberParseException as e:
                issues.append(ValidationIssue(
                    field='phone',
                    value=phone,
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.FORMAT,
                    message=f"Cannot parse phone number: {phone} ({e.error_type.name})",
                    suggestion=self._suggest_phone_fix(phone),
                    rule_name='phone_parse_error'
                ))
        else:
            # Fallback validation using regex patterns
            self._validate_phone_with_patterns(phone, issues)
        
        return issues
    
    def _validate_phone_with_patterns(self, phone: str, issues: List[ValidationIssue]) -> None:
        """Fallback phone validation using regex patterns when phonenumbers is not available."""
        # Try to match against known country patterns
        phone_clean = re.sub(r'[^\d+]', '', phone)
        
        matched_pattern = False
        for country, pattern in self.country_patterns.items():
            if re.match(pattern, phone_clean):
                matched_pattern = True
                break
        
        if not matched_pattern:
            # Try generic international pattern
            if re.match(r'^\+?[1-9]\d{7,14}$', phone_clean):
                matched_pattern = True
        
        if not matched_pattern:
            issues.append(ValidationIssue(
                field='phone',
                value=phone,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.FORMAT,
                message=f"Phone number format not recognized: {phone}",
                suggestion=self._suggest_phone_fix(phone),
                rule_name='phone_format_unrecognized'
            ))
    
    def _validate_phone_format(self, phone: str) -> List[ValidationIssue]:
        """Basic phone format validation."""
        issues = []
        
        # Remove common formatting characters for analysis
        digits_only = re.sub(r'[^\d+]', '', phone)
        
        # Length checks
        if len(digits_only) < 8:
            issues.append(ValidationIssue(
                field='phone',
                value=phone,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message=f"Phone number too short: {phone}",
                suggestion="Phone numbers should be at least 8 digits",
                rule_name='phone_too_short'
            ))
        elif len(digits_only) > 15:
            issues.append(ValidationIssue(
                field='phone',
                value=phone,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message=f"Phone number too long: {phone}",
                suggestion="Phone numbers should not exceed 15 digits",
                rule_name='phone_too_long'
            ))
        
        # Check for suspicious patterns
        if digits_only.replace('+', '').isdigit():
            digits = digits_only.replace('+', '')
            
            # All same digit
            if len(set(digits)) == 1:
                issues.append(ValidationIssue(
                    field='phone',
                    value=phone,
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DATA_QUALITY,
                    message=f"Phone number has suspicious pattern (all same digit): {phone}",
                    suggestion="Verify this is a real phone number",
                    rule_name='phone_suspicious_pattern'
                ))
            
            # Sequential digits
            if self._is_sequential(digits):
                issues.append(ValidationIssue(
                    field='phone',
                    value=phone,
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DATA_QUALITY,
                    message=f"Phone number has suspicious pattern (sequential): {phone}",
                    suggestion="Verify this is a real phone number",
                    rule_name='phone_sequential'
                ))
        
        return issues
    
    def _is_sequential(self, digits: str) -> bool:
        """Check if digits are in sequential order."""
        if len(digits) < 4:
            return False
        
        # Check for ascending sequence
        ascending = all(int(digits[i]) == int(digits[i-1]) + 1 for i in range(1, min(5, len(digits))))
        
        # Check for descending sequence
        descending = all(int(digits[i]) == int(digits[i-1]) - 1 for i in range(1, min(5, len(digits))))
        
        return ascending or descending
    
    def _suggest_phone_fix(self, phone: str) -> str:
        """Suggest fixes for invalid phone numbers."""
        if not phone:
            return "Provide a valid phone number"
        
        # Remove non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        if not cleaned:
            return "Phone number must contain digits"
        
        if len(cleaned) < 8:
            return "Phone number is too short (minimum 8 digits)"
        
        if len(cleaned) > 15:
            return "Phone number is too long (maximum 15 digits)"
        
        if not cleaned.startswith('+') and len(cleaned) >= 10:
            return f"Consider adding country code: +1{cleaned} (for US numbers)"
        
        return "Check phone number format (example: +1-555-123-4567)"


class BusinessRuleValidator:
    """Validator for business-specific rules and data quality."""
    
    def __init__(self):
        """Initialize business rule validator."""
        # Common company suffixes
        self.company_suffixes = {
            'inc', 'incorporated', 'corp', 'corporation', 'llc', 'ltd', 'limited',
            'co', 'company', 'group', 'holdings', 'enterprises', 'solutions',
            'services', 'systems', 'technologies', 'tech', 'consulting'
        }
        
        # Suspicious name patterns
        self.suspicious_name_patterns = [
            r'^\d+$',  # All numbers
            r'^test\d*$',  # Test entries
            r'^sample\d*$',  # Sample entries
            r'^example\d*$',  # Example entries
            r'^[a-z]+$',  # All lowercase (might be valid but suspicious)
            r'^[A-Z]+$',  # All uppercase (might be valid but suspicious)
        ]
    
    def validate_name(self, name: str) -> List[ValidationIssue]:
        """Validate person name with business rules."""
        issues = []
        
        if not name or not name.strip():
            issues.append(ValidationIssue(
                field='name',
                value=name,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Name is required",
                rule_name='name_required'
            ))
            return issues
        
        name = name.strip()
        
        # Length validation
        if len(name) < 2:
            issues.append(ValidationIssue(
                field='name',
                value=name,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message=f"Name too short: {name}",
                suggestion="Names should be at least 2 characters long",
                rule_name='name_too_short'
            ))
        elif len(name) > 100:
            issues.append(ValidationIssue(
                field='name',
                value=name,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.FORMAT,
                message=f"Name unusually long: {name}",
                suggestion="Verify this is a complete name",
                rule_name='name_too_long'
            ))
        
        # Pattern validation
        for pattern in self.suspicious_name_patterns:
            if re.match(pattern, name.lower()):
                issues.append(ValidationIssue(
                    field='name',
                    value=name,
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DATA_QUALITY,
                    message=f"Suspicious name pattern: {name}",
                    suggestion="Verify this is a real person's name",
                    rule_name='name_suspicious_pattern'
                ))
                break
        
        # Check for valid name characters
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            issues.append(ValidationIssue(
                field='name',
                value=name,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.FORMAT,
                message=f"Name contains unusual characters: {name}",
                suggestion="Names typically contain only letters, spaces, hyphens, and apostrophes",
                rule_name='name_unusual_characters'
            ))
        
        # Check for proper capitalization
        if name.isupper():
            issues.append(ValidationIssue(
                field='name',
                value=name,
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.FORMAT,
                message="Name is in all caps",
                suggestion=f"Consider proper case: {name.title()}",
                rule_name='name_all_caps'
            ))
        elif name.islower():
            issues.append(ValidationIssue(
                field='name',
                value=name,
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.FORMAT,
                message="Name is in all lowercase",
                suggestion=f"Consider proper case: {name.title()}",
                rule_name='name_all_lowercase'
            ))
        
        return issues
    
    def validate_company(self, company: str) -> List[ValidationIssue]:
        """Validate company name with business rules."""
        issues = []
        
        if not company or not company.strip():
            issues.append(ValidationIssue(
                field='company',
                value=company,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message="Company name is required",
                rule_name='company_required'
            ))
            return issues
        
        company = company.strip()
        
        # Length validation
        if len(company) < 2:
            issues.append(ValidationIssue(
                field='company',
                value=company,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.FORMAT,
                message=f"Company name too short: {company}",
                suggestion="Company names should be at least 2 characters long",
                rule_name='company_too_short'
            ))
        elif len(company) > 200:
            issues.append(ValidationIssue(
                field='company',
                value=company,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.FORMAT,
                message=f"Company name unusually long: {company}",
                suggestion="Verify this is a complete company name",
                rule_name='company_too_long'
            ))
        
        # Check for suspicious patterns
        if re.match(r'^\d+$', company):
            issues.append(ValidationIssue(
                field='company',
                value=company,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                message=f"Company name is all numbers: {company}",
                suggestion="Verify this is a real company name",
                rule_name='company_all_numbers'
            ))
        
        # Check for test/sample entries
        test_patterns = ['test', 'sample', 'example', 'demo', 'placeholder']
        if any(pattern in company.lower() for pattern in test_patterns):
            issues.append(ValidationIssue(
                field='company',
                value=company,
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                message=f"Company name appears to be test data: {company}",
                suggestion="Replace with actual company name",
                rule_name='company_test_data'
            ))
        
        # Suggest adding company suffix if missing
        company_lower = company.lower()
        has_suffix = any(suffix in company_lower for suffix in self.company_suffixes)
        
        if not has_suffix and len(company.split()) == 1:
            issues.append(ValidationIssue(
                field='company',
                value=company,
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.BUSINESS_RULE,
                message="Company name may be missing legal suffix",
                suggestion="Consider adding suffix like 'Inc', 'LLC', 'Corp', etc.",
                rule_name='company_missing_suffix'
            ))
        
        return issues


class AdvancedDataValidator:
    """
    Comprehensive data validation framework combining all validators.
    """
    
    def __init__(self, enable_domain_checking: bool = True):
        """
        Initialize the advanced data validator.
        
        Args:
            enable_domain_checking: Whether to enable DNS domain checking
        """
        self.email_validator = EmailValidator()
        self.phone_validator = PhoneValidator()
        self.business_validator = BusinessRuleValidator()
        self.enable_domain_checking = enable_domain_checking
    
    def validate_customer_data(self, customer_data: Dict[str, Any]) -> ValidationResult:
        """
        Comprehensive validation of customer data.
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Complete validation result
        """
        all_issues = []
        
        # Validate each field
        if 'name' in customer_data:
            name_issues = self.business_validator.validate_name(customer_data['name'])
            all_issues.extend(name_issues)
        
        if 'company' in customer_data:
            company_issues = self.business_validator.validate_company(customer_data['company'])
            all_issues.extend(company_issues)
        
        if 'email' in customer_data:
            email_issues = self.email_validator.validate_email(
                customer_data['email'], 
                check_domain=self.enable_domain_checking
            )
            all_issues.extend(email_issues)
        
        if 'phone' in customer_data:
            phone_issues = self.phone_validator.validate_phone(customer_data['phone'])
            all_issues.extend(phone_issues)
        
        # Cross-field validation
        cross_field_issues = self._validate_cross_field_rules(customer_data)
        all_issues.extend(cross_field_issues)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(all_issues, customer_data)
        
        # Generate suggestions
        suggestions = self._generate_improvement_suggestions(all_issues, customer_data)
        
        # Determine if data is valid (no errors)
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in all_issues)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=all_issues,
            quality_score=quality_score,
            suggestions=suggestions
        )
    
    def _validate_cross_field_rules(self, customer_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate rules that span multiple fields."""
        issues = []
        
        # Check for consistency between name and email
        if 'name' in customer_data and 'email' in customer_data:
            name = customer_data['name'].strip().lower()
            email = customer_data['email'].strip().lower()
            
            if '@' in email:
                email_local = email.split('@')[0]
                name_parts = name.split()
                
                # Check if email local part contains name parts
                name_in_email = any(part in email_local for part in name_parts if len(part) > 2)
                
                if not name_in_email and len(name_parts) > 0:
                    issues.append(ValidationIssue(
                        field='email',
                        value=email,
                        severity=ValidationSeverity.INFO,
                        category=ValidationCategory.CONSISTENCY,
                        message="Email address doesn't appear to match the person's name",
                        suggestion="Verify email belongs to the named person",
                        rule_name='email_name_consistency'
                    ))
        
        # Check for placeholder data
        placeholder_patterns = ['example', 'test', 'sample', 'placeholder', 'dummy']
        for field, value in customer_data.items():
            if isinstance(value, str) and value.strip():
                value_lower = value.lower()
                if any(pattern in value_lower for pattern in placeholder_patterns):
                    issues.append(ValidationIssue(
                        field=field,
                        value=value,
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.DATA_QUALITY,
                        message=f"Field appears to contain placeholder data: {value}",
                        suggestion="Replace with actual data",
                        rule_name='placeholder_data'
                    ))
        
        return issues
    
    def _calculate_quality_score(self, issues: List[ValidationIssue], customer_data: Dict[str, Any]) -> float:
        """Calculate overall data quality score (0-100)."""
        if not customer_data:
            return 0.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 20.0  # Major deduction for errors
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 10.0  # Moderate deduction for warnings
            elif issue.severity == ValidationSeverity.INFO:
                score -= 2.0   # Minor deduction for info issues
        
        # Bonus for completeness
        required_fields = ['name', 'company', 'email', 'phone']
        complete_fields = sum(1 for field in required_fields if customer_data.get(field, '').strip())
        completeness_bonus = (complete_fields / len(required_fields)) * 10.0
        score += completeness_bonus
        
        return max(0.0, min(100.0, score))
    
    def _generate_improvement_suggestions(self, issues: List[ValidationIssue], customer_data: Dict[str, Any]) -> List[str]:
        """Generate actionable suggestions for data improvement."""
        suggestions = []
        
        # Collect suggestions from issues
        for issue in issues:
            if issue.suggestion and issue.suggestion not in suggestions:
                suggestions.append(issue.suggestion)
        
        # Add general suggestions based on data quality
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        
        if error_count > 0:
            suggestions.append(f"Fix {error_count} critical error(s) before proceeding")
        
        if warning_count > 2:
            suggestions.append("Review and address data quality warnings")
        
        # Check for missing fields
        required_fields = ['name', 'company', 'email', 'phone']
        missing_fields = [field for field in required_fields if not customer_data.get(field, '').strip()]
        
        if missing_fields:
            suggestions.append(f"Complete missing required fields: {', '.join(missing_fields)}")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def validate_batch_data(self, data_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of customer data records.
        
        Args:
            data_records: List of customer data dictionaries
            
        Returns:
            Batch validation summary
        """
        results = []
        total_issues = 0
        total_errors = 0
        total_warnings = 0
        quality_scores = []
        
        for i, record in enumerate(data_records):
            result = self.validate_customer_data(record)
            results.append({
                'record_index': i,
                'result': result
            })
            
            total_issues += len(result.issues)
            total_errors += result.error_count
            total_warnings += result.warning_count
            quality_scores.append(result.quality_score)
        
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        valid_records = sum(1 for r in results if r['result'].is_valid)
        
        return {
            'total_records': len(data_records),
            'valid_records': valid_records,
            'invalid_records': len(data_records) - valid_records,
            'total_issues': total_issues,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'average_quality_score': avg_quality_score,
            'validation_results': results
        }