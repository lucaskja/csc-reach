"""
Locale-specific formatting utilities for CSC-Reach.
Handles date, time, number, currency, and address formatting based on user locale.
"""

import re
from datetime import datetime, date, time
from typing import Dict, Any, Optional, Union
from decimal import Decimal

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LocaleFormatter:
    """
    Handles locale-specific formatting for dates, numbers, currencies, and addresses.
    """
    
    def __init__(self, i18n_manager):
        """
        Initialize the locale formatter.
        
        Args:
            i18n_manager: I18n manager instance for getting locale settings
        """
        self.i18n_manager = i18n_manager
    
    def format_date(self, date_obj: Union[datetime, date], format_key: str = "date_format") -> str:
        """
        Format a date according to current locale.
        
        Args:
            date_obj: Date object to format
            format_key: Translation key for date format
            
        Returns:
            Formatted date string
        """
        try:
            format_string = self.i18n_manager.translate(format_key)
            
            # Convert format string from translation format to Python format
            # MM/dd/yyyy -> %m/%d/%Y
            # dd/MM/yyyy -> %d/%m/%Y
            python_format = format_string.replace('yyyy', '%Y').replace('MM', '%m').replace('dd', '%d')
            
            if isinstance(date_obj, datetime):
                return date_obj.strftime(python_format)
            elif isinstance(date_obj, date):
                return date_obj.strftime(python_format)
            else:
                return str(date_obj)
                
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return str(date_obj)
    
    def format_time(self, time_obj: Union[datetime, time], format_key: str = "time_format") -> str:
        """
        Format a time according to current locale.
        
        Args:
            time_obj: Time object to format
            format_key: Translation key for time format
            
        Returns:
            Formatted time string
        """
        try:
            format_string = self.i18n_manager.translate(format_key)
            
            # Convert format string from translation format to Python format
            # h:mm:ss tt -> %I:%M:%S %p
            # HH:mm:ss -> %H:%M:%S
            python_format = (format_string
                           .replace('HH', '%H')
                           .replace('h', '%I')
                           .replace('mm', '%M')
                           .replace('ss', '%S')
                           .replace('tt', '%p'))
            
            if isinstance(time_obj, datetime):
                return time_obj.strftime(python_format)
            elif isinstance(time_obj, time):
                return time_obj.strftime(python_format)
            else:
                return str(time_obj)
                
        except Exception as e:
            logger.error(f"Error formatting time: {e}")
            return str(time_obj)
    
    def format_datetime(self, datetime_obj: datetime, format_key: str = "datetime_format") -> str:
        """
        Format a datetime according to current locale.
        
        Args:
            datetime_obj: Datetime object to format
            format_key: Translation key for datetime format
            
        Returns:
            Formatted datetime string
        """
        try:
            format_string = self.i18n_manager.translate(format_key)
            
            # Convert format string from translation format to Python format
            python_format = (format_string
                           .replace('yyyy', '%Y')
                           .replace('MM', '%m')
                           .replace('dd', '%d')
                           .replace('HH', '%H')
                           .replace('h', '%I')
                           .replace('mm', '%M')
                           .replace('ss', '%S')
                           .replace('tt', '%p'))
            
            return datetime_obj.strftime(python_format)
                
        except Exception as e:
            logger.error(f"Error formatting datetime: {e}")
            return str(datetime_obj)
    
    def format_number(self, number: Union[int, float, Decimal], decimal_places: Optional[int] = None) -> str:
        """
        Format a number according to current locale.
        
        Args:
            number: Number to format
            decimal_places: Number of decimal places (None for auto)
            
        Returns:
            Formatted number string
        """
        try:
            decimal_sep = self.i18n_manager.translate("number_decimal_separator")
            thousands_sep = self.i18n_manager.translate("number_thousands_separator")
            
            # Convert to string with appropriate decimal places
            if decimal_places is not None:
                number_str = f"{float(number):.{decimal_places}f}"
            else:
                number_str = str(number)
            
            # Split into integer and decimal parts
            if '.' in number_str:
                integer_part, decimal_part = number_str.split('.')
            else:
                integer_part, decimal_part = number_str, ""
            
            # Add thousands separators
            if len(integer_part) > 3:
                # Add separators from right to left
                formatted_integer = ""
                for i, digit in enumerate(reversed(integer_part)):
                    if i > 0 and i % 3 == 0:
                        formatted_integer = thousands_sep + formatted_integer
                    formatted_integer = digit + formatted_integer
                integer_part = formatted_integer
            
            # Combine parts
            if decimal_part:
                return f"{integer_part}{decimal_sep}{decimal_part}"
            else:
                return integer_part
                
        except Exception as e:
            logger.error(f"Error formatting number: {e}")
            return str(number)
    
    def format_currency(self, amount: Union[int, float, Decimal], decimal_places: int = 2) -> str:
        """
        Format a currency amount according to current locale.
        
        Args:
            amount: Currency amount to format
            decimal_places: Number of decimal places
            
        Returns:
            Formatted currency string
        """
        try:
            currency_symbol = self.i18n_manager.translate("currency_symbol")
            currency_position = self.i18n_manager.translate("currency_position")
            
            # Format the number part
            formatted_number = self.format_number(amount, decimal_places)
            
            # Position the currency symbol
            if currency_position == "before":
                return f"{currency_symbol}{formatted_number}"
            else:  # after
                return f"{formatted_number} {currency_symbol}"
                
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"${amount:.2f}"  # Fallback to USD format
    
    def format_phone(self, phone_number: str, country_code: Optional[str] = None) -> str:
        """
        Format a phone number according to current locale.
        
        Args:
            phone_number: Phone number to format
            country_code: Optional country code override
            
        Returns:
            Formatted phone number string
        """
        try:
            # Use country-specific format if provided
            if country_code:
                format_key = f"phone_format_{country_code.lower()}"
                phone_format = self.i18n_manager.translate(format_key)
                if phone_format == format_key:  # Translation not found
                    phone_format = self.i18n_manager.translate("phone_format")
            else:
                phone_format = self.i18n_manager.translate("phone_format")
            
            # Remove all non-digit characters from input
            digits_only = re.sub(r'\D', '', phone_number)
            
            # Handle international format
            if digits_only.startswith('1') and len(digits_only) == 11:
                # US/Canada number with country code
                digits_only = digits_only[1:]  # Remove leading 1
            
            # Apply format pattern
            formatted = phone_format
            for digit in digits_only:
                formatted = formatted.replace('#', digit, 1)
            
            # Remove any remaining # characters
            formatted = formatted.replace('#', '')
            
            return formatted
                
        except Exception as e:
            logger.error(f"Error formatting phone number: {e}")
            return phone_number
    
    def format_address(self, address_data: Dict[str, str]) -> str:
        """
        Format an address according to current locale.
        
        Args:
            address_data: Dictionary with address components
                         (street, city, state, zip, country)
            
        Returns:
            Formatted address string
        """
        try:
            address_format = self.i18n_manager.translate("address_format")
            
            # Replace placeholders with actual data
            formatted_address = address_format.format(**address_data)
            
            # Clean up any empty lines
            lines = [line.strip() for line in formatted_address.split('\n') if line.strip()]
            
            return '\n'.join(lines)
                
        except Exception as e:
            logger.error(f"Error formatting address: {e}")
            # Fallback to simple format
            return f"{address_data.get('street', '')}\n{address_data.get('city', '')}, {address_data.get('state', '')} {address_data.get('zip', '')}\n{address_data.get('country', '')}"
    
    def parse_date(self, date_string: str, format_key: str = "date_format") -> Optional[date]:
        """
        Parse a date string according to current locale format.
        
        Args:
            date_string: Date string to parse
            format_key: Translation key for date format
            
        Returns:
            Parsed date object or None if parsing fails
        """
        try:
            format_string = self.i18n_manager.translate(format_key)
            
            # Convert format string from translation format to Python format
            python_format = format_string.replace('yyyy', '%Y').replace('MM', '%m').replace('dd', '%d')
            
            parsed_date = datetime.strptime(date_string, python_format).date()
            return parsed_date
                
        except Exception as e:
            logger.error(f"Error parsing date '{date_string}': {e}")
            return None
    
    def parse_number(self, number_string: str) -> Optional[float]:
        """
        Parse a number string according to current locale format.
        
        Args:
            number_string: Number string to parse
            
        Returns:
            Parsed number or None if parsing fails
        """
        try:
            decimal_sep = self.i18n_manager.translate("number_decimal_separator")
            thousands_sep = self.i18n_manager.translate("number_thousands_separator")
            
            # Remove thousands separators
            cleaned = number_string.replace(thousands_sep, '')
            
            # Replace decimal separator with standard dot
            if decimal_sep != '.':
                cleaned = cleaned.replace(decimal_sep, '.')
            
            return float(cleaned)
                
        except Exception as e:
            logger.error(f"Error parsing number '{number_string}': {e}")
            return None
    
    def format_percentage(self, value: Union[int, float], decimal_places: int = 1) -> str:
        """
        Format a percentage according to current locale.
        
        Args:
            value: Percentage value (0.0 to 1.0 or 0 to 100)
            decimal_places: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        try:
            # Convert to percentage if value is between 0 and 1
            if 0 <= value <= 1:
                percentage_value = value * 100
            else:
                percentage_value = value
            
            formatted_number = self.format_number(percentage_value, decimal_places)
            return f"{formatted_number}%"
                
        except Exception as e:
            logger.error(f"Error formatting percentage: {e}")
            return f"{value}%"
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size according to current locale.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted file size string
        """
        try:
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            size = float(size_bytes)
            unit_index = 0
            
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            
            if unit_index == 0:
                return f"{int(size)} {units[unit_index]}"
            else:
                formatted_size = self.format_number(size, 1)
                return f"{formatted_size} {units[unit_index]}"
                
        except Exception as e:
            logger.error(f"Error formatting file size: {e}")
            return f"{size_bytes} B"
    
    def format_duration(self, seconds: int) -> str:
        """
        Format duration according to current locale.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        try:
            if seconds < 60:
                return self.i18n_manager.translate_plural("second", seconds, count=seconds)
            elif seconds < 3600:
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                if remaining_seconds == 0:
                    return self.i18n_manager.translate_plural("minute", minutes, count=minutes)
                else:
                    return f"{self.i18n_manager.translate_plural('minute', minutes, count=minutes)}, {self.i18n_manager.translate_plural('second', remaining_seconds, count=remaining_seconds)}"
            else:
                hours = seconds // 3600
                remaining_minutes = (seconds % 3600) // 60
                if remaining_minutes == 0:
                    return self.i18n_manager.translate_plural("hour", hours, count=hours)
                else:
                    return f"{self.i18n_manager.translate_plural('hour', hours, count=hours)}, {self.i18n_manager.translate_plural('minute', remaining_minutes, count=remaining_minutes)}"
                
        except Exception as e:
            logger.error(f"Error formatting duration: {e}")
            return f"{seconds}s"
    
    def format_relative_time(self, target_datetime: datetime) -> str:
        """
        Format relative time (e.g., "2 hours ago", "in 3 days").
        
        Args:
            target_datetime: Target datetime to compare with now
            
        Returns:
            Formatted relative time string
        """
        try:
            now = datetime.now()
            diff = target_datetime - now
            abs_diff = abs(diff.total_seconds())
            
            if abs_diff < 60:
                # Less than a minute
                if diff.total_seconds() >= 0:
                    return self.i18n_manager.translate("relative_time_now")
                else:
                    return self.i18n_manager.translate("relative_time_just_now")
            elif abs_diff < 3600:
                # Less than an hour
                minutes = int(abs_diff // 60)
                if diff.total_seconds() >= 0:
                    return self.i18n_manager.translate("relative_time_in_minutes", count=minutes)
                else:
                    return self.i18n_manager.translate("relative_time_minutes_ago", count=minutes)
            elif abs_diff < 86400:
                # Less than a day
                hours = int(abs_diff // 3600)
                if diff.total_seconds() >= 0:
                    return self.i18n_manager.translate("relative_time_in_hours", count=hours)
                else:
                    return self.i18n_manager.translate("relative_time_hours_ago", count=hours)
            else:
                # Days or more
                days = int(abs_diff // 86400)
                if diff.total_seconds() >= 0:
                    return self.i18n_manager.translate("relative_time_in_days", count=days)
                else:
                    return self.i18n_manager.translate("relative_time_days_ago", count=days)
                
        except Exception as e:
            logger.error(f"Error formatting relative time: {e}")
            return self.format_datetime(target_datetime)
    
    def get_locale_info(self) -> Dict[str, Any]:
        """
        Get current locale formatting information.
        
        Returns:
            Dictionary with locale formatting settings
        """
        lang_info = self.i18n_manager.get_language_info(self.i18n_manager.get_current_language())
        
        return {
            'language': self.i18n_manager.get_current_language(),
            'language_name': lang_info.get('name', ''),
            'native_name': lang_info.get('native', ''),
            'direction': lang_info.get('direction', 'ltr'),
            'is_rtl': lang_info.get('is_rtl', False),
            'region': lang_info.get('region', ''),
            'date_format': self.i18n_manager.translate("date_format"),
            'time_format': self.i18n_manager.translate("time_format"),
            'datetime_format': self.i18n_manager.translate("datetime_format"),
            'decimal_separator': self.i18n_manager.translate("number_decimal_separator"),
            'thousands_separator': self.i18n_manager.translate("number_thousands_separator"),
            'currency_symbol': self.i18n_manager.translate("currency_symbol"),
            'currency_position': self.i18n_manager.translate("currency_position"),
            'phone_format': self.i18n_manager.translate("phone_format"),
            'address_format': self.i18n_manager.translate("address_format")
        }


# Global formatter instance
_locale_formatter = None

def get_locale_formatter():
    """Get global locale formatter instance."""
    global _locale_formatter
    if _locale_formatter is None:
        from .i18n_manager import get_i18n_manager
        _locale_formatter = LocaleFormatter(get_i18n_manager())
    return _locale_formatter